"""LangChain tools the shopping-guide LLM is allowed to call.

Design constraints (per user requirements):
1. The LLM must NOT touch the database directly. It can only invoke these tools.
2. The tools are strictly QUERY-ONLY. No insert / update / delete operations.
3. The guide must NOT place orders for the user. It can only recommend products;
   the user clicks a product card to place an order on the frontend.

Tools provided:
- search_products_by_keyword: semantic + structured-facet retrieval over the product
  vector store, with optional cross-encoder reranking.
- get_product_detail: fetch a single product's full info by product_id.
- search_knowledge_base: retrieval over non-product knowledge docs (policy / FAQ / etc).
"""
import json
import logging
from typing import Optional

from langchain_core.tools import tool
from pydantic import BaseModel, Field

from app.config import settings
from app.core.reranker import rerank_scores
from app.core.vector_store import get_vector_store
from app.storage.models import Product
from app.storage.database import SessionLocal

log = logging.getLogger(__name__)


# === Tool input schemas ===
class SearchProductsInput(BaseModel):
    keyword: str = Field(..., description="用户的搜索关键词或商品需求描述,如'卧室音箱 预算500'")
    top_k: int = Field(default=8, ge=1, le=12, description="返回商品数量,默认8,最多12")
    category: Optional[str] = Field(default="", description="品类精确过滤,如'蓝牙耳机''充电宝';不确定或不限时留空")
    brand: Optional[str] = Field(default="", description="品牌精确过滤,如'小米''漫步者';不确定或不限时留空")
    min_price: Optional[float] = Field(default=None, description="预算下限(元),用户明确说了最低预算时才填")
    max_price: Optional[float] = Field(default=None, description="预算上限(元),用户明确说了预算/不超过X元时填")
    in_stock: Optional[bool] = Field(default=None, description="是否只看有货商品;true=只要有货,不填=不限")


class GetProductDetailInput(BaseModel):
    product_id: str = Field(..., description="商品 ID,必须是 search_products_by_keyword 返回结果中的 product_id 字段值(UUID 格式,如 '4dcc30c231ae4022b2df4ac37e78b9a5'),不能用序号'1''2'代替")


class SearchKnowledgeInput(BaseModel):
    query: str = Field(..., description="用户问题关键词,用于检索平台知识库文档(如售后政策、退换货规则、发票、物流、平台规则、常见FAQ等)")
    top_k: int = Field(default=4, ge=1, le=8, description="返回的文档片段数量,默认4")


# === Retrieval helpers ===
# Facet drop priority for graceful relaxation: softest first, 品类 last.
_DROP_ORDER = ["brand", "min_price", "max_price", "in_stock", "category"]
_FACET_LABELS = {
    "brand": "品牌",
    "min_price": "价格下限",
    "max_price": "价格上限",
    "in_stock": "仅看有货",
    "category": "品类",
}


def _specified_facets(category, brand, min_price, max_price, in_stock) -> set:
    """Which facets the caller actually specified (so we only relax those)."""
    facets: set = set()
    if category:
        facets.add("category")
    if brand:
        facets.add("brand")
    if in_stock is not None:
        facets.add("in_stock")
    if min_price is not None and min_price > 0:
        facets.add("min_price")
    if max_price is not None and max_price > 0:
        facets.add("max_price")
    return facets


def _build_where(
    keep: set,
    category: str,
    brand: str,
    min_price: Optional[float],
    max_price: Optional[float],
    in_stock: Optional[bool],
) -> dict:
    """Build a Chroma `where` filter using only the facets present in `keep`.

    NOTE: each price bound is a SEPARATE condition — Chroma rejects two operators
    ($gte and $lte) on the same key within one dict.
    """
    conds: list[dict] = [{"type": "product"}]
    if "category" in keep and category:
        conds.append({"category": {"$eq": category}})
    if "brand" in keep and brand:
        conds.append({"brand": {"$eq": brand}})
    if "in_stock" in keep and in_stock is not None:
        conds.append({"in_stock": bool(in_stock)})
    if "min_price" in keep and min_price is not None and min_price > 0:
        conds.append({"price_value": {"$gte": float(min_price)}})
    if "max_price" in keep and max_price is not None and max_price > 0:
        conds.append({"price_value": {"$lte": float(max_price)}})
    return conds[0] if len(conds) == 1 else {"$and": conds}


def _relaxation_levels(specified: set) -> list[set]:
    """Full facet set -> progressively looser keep-sets (brand dropped before
    price before category). The final level is the empty set (type=product only).
    """
    levels = [set(specified)]
    cur = set(specified)
    for f in _DROP_ORDER:
        if f in cur:
            cur = cur - {f}
            levels.append(set(cur))
    return levels


def _collect_candidates(results, sim_threshold: float) -> list[dict]:
    """Dedup + threshold-filter raw Chroma results into candidate dicts."""
    out: list[dict] = []
    seen: set[str] = set()
    for doc, distance in results:
        meta = doc.metadata or {}
        if meta.get("type") != "product":
            continue
        pid = meta.get("product_id") or ""
        if not pid or pid in seen:
            continue
        similarity = max(0.0, 1.0 - float(distance) / 2.0)
        if similarity < sim_threshold:
            continue
        seen.add(pid)
        out.append(
            {
                "pid": pid,
                "meta": meta,
                "text": doc.page_content or "",
                "similarity": similarity,
            }
        )
    return out


# === Tool implementations ===
@tool("search_products_by_keyword", args_schema=SearchProductsInput)
def search_products_by_keyword(
    keyword: str,
    top_k: int = 8,
    category: str = "",
    brand: str = "",
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    in_stock: Optional[bool] = None,
) -> str:
    """根据用户需求/关键词检索商品,返回精简信息(名称、价格、品牌、品类、相似度、product_id)。

    使用此工具查找与用户需求相关的商品。用户通常会描述用途、预算、品牌、品类等偏好。
    【提升准确率】当用户明确了预算/品牌/品类时,务必同时填写对应的结构化过滤参数
    (min_price/max_price/brand/category/in_stock),系统会先精确过滤再语义排序,比只塞进
    keyword 更准。例如"300元以内的小米蓝牙耳机"应设 max_price=300、brand="小米"、category="蓝牙耳机"。
    当有多个相似商品都符合需求时,应尽量返回更多结果(top_k 6-12)供用户对比选择。
    """
    try:
        vs = get_vector_store()
    except Exception as e:
        log.exception("Vector store init failed: %s", e)
        return json.dumps({"error": "向量库初始化失败", "products": []}, ensure_ascii=False)

    sim_threshold = settings.retrieval_similarity_threshold
    candidate_k = max(settings.retrieval_candidate_k, top_k * 3)

    # Graduated relaxation: try the full facet filter first; if it yields nothing,
    # drop the softest constraint (brand) then price, keeping 品类 until last, so we
    # still recommend something while honoring the user's most important constraints.
    specified = _specified_facets(category, brand, min_price, max_price, in_stock)
    candidates: list[dict] = []
    winning_keep = set(specified)
    try:
        for keep in _relaxation_levels(specified):
            where = _build_where(keep, category, brand, min_price, max_price, in_stock)
            results = vs.similarity_search_with_score(keyword, k=candidate_k, filter=where)
            candidates = _collect_candidates(results, sim_threshold)
            if candidates:
                winning_keep = keep
                break
    except Exception as e:
        log.exception("Similarity search failed: %s", e)
        return json.dumps({"error": f"检索失败: {e}", "products": []}, ensure_ascii=False)

    if not candidates:
        return json.dumps({"products": [], "relaxed": []}, ensure_ascii=False)

    # Facets the user asked for but had to be dropped to get any result
    relaxed = [_FACET_LABELS[f] for f in (specified - winning_keep)]

    # Cross-encoder rerank for precision; degrades to vector similarity if unavailable
    scores = rerank_scores(keyword, [c["text"] for c in candidates])
    if scores is not None:
        for c, s in zip(candidates, scores):
            c["rerank"] = s
        candidates.sort(key=lambda c: c["rerank"], reverse=True)
    else:
        candidates.sort(key=lambda c: c["similarity"], reverse=True)

    products = []
    for c in candidates[:top_k]:
        meta = c["meta"]
        products.append(
            {
                "product_id": c["pid"],
                "name": meta.get("name", "未知"),
                "price": meta.get("price", ""),
                "brand": meta.get("brand", ""),
                "category": meta.get("category", ""),
                "snippet": c["text"][:300],
                "similarity": round(c["similarity"], 4),
            }
        )

    return json.dumps({"products": products, "relaxed": relaxed}, ensure_ascii=False)


@tool("get_product_detail", args_schema=GetProductDetailInput)
def get_product_detail(product_id: str) -> str:
    """根据 product_id 查询单个商品的完整信息(名称、描述、规格、价格、库存状态)。

    当用户对某个推荐商品询问更多细节时使用此工具。
    【重要】product_id 必须是 search_products_by_keyword 返回结果中的 product_id 字段值,
    是 UUID 格式(如 '4dcc30c231ae4022b2df4ac37e78b9a5'),不能用序号 '1' '2' 代替。
    如果用户说"看看第一个",请从之前的搜索结果中取第一个商品的 product_id。
    """
    db = SessionLocal()
    try:
        p = db.get(Product, product_id)
        if not p:
            return json.dumps({"error": "商品不存在"}, ensure_ascii=False)
        return json.dumps(
            {
                "product_id": p.id,
                "name": p.name,
                "description": p.description or "",
                "detail_content": p.detail_content or "",
                "price": p.price or "",
                "specs": p.specs or "",
                "stock_status": "充足" if (p.stock or 0) > 0 else "缺货",
                "merchant_id": p.merchant_id,
            },
            ensure_ascii=False,
        )
    finally:
        db.close()


@tool("search_knowledge_base", args_schema=SearchKnowledgeInput)
def search_knowledge_base(query: str, top_k: int = 4) -> str:
    """检索平台知识库文档(售后政策、退换货规则、发票、物流、平台规则、常见FAQ 等非商品信息)。

    当用户询问与具体商品无关的政策、规则、流程类问题时使用此工具。
    只返回知识库文档片段,不会返回商品(商品请用 search_products_by_keyword)。
    """
    try:
        vs = get_vector_store()
    except Exception as e:
        log.exception("Vector store init failed: %s", e)
        return json.dumps({"error": "向量库初始化失败", "documents": []}, ensure_ascii=False)

    try:
        results = vs.similarity_search_with_score(query, k=max(top_k * 3, 12))
    except Exception as e:
        log.exception("Knowledge search failed: %s", e)
        return json.dumps({"error": f"检索失败: {e}", "documents": []}, ensure_ascii=False)

    sim_threshold = settings.retrieval_similarity_threshold
    documents = []
    for doc, distance in results:
        meta = doc.metadata or {}
        # Skip product vectors; they are handled by search_products_by_keyword
        if meta.get("type") == "product":
            continue
        similarity = max(0.0, 1.0 - float(distance) / 2.0)
        if similarity < sim_threshold:
            continue
        documents.append(
            {
                "source": meta.get("source", "未知"),
                "snippet": (doc.page_content or "")[:500],
                "similarity": round(similarity, 4),
            }
        )
        if len(documents) >= top_k:
            break

    return json.dumps({"documents": documents}, ensure_ascii=False)


# Registry exported for chain.py to bind to the LLM
SHOPPING_TOOLS = [search_products_by_keyword, get_product_detail, search_knowledge_base]
