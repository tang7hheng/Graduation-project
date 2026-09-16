"""LangChain tools the shopping-guide LLM is allowed to call.

Design constraints (per user requirements):
1. The LLM must NOT touch the database directly. It can only invoke these tools.
2. The tools are strictly QUERY-ONLY. No insert / update / delete operations.
3. The guide must NOT place orders for the user. It can only recommend products;
   the user clicks a product card to place an order on the frontend.

Tools provided:
- search_products_by_keyword: semantic retrieval over the product vector store.
- get_product_detail: fetch a single product's full info by product_id.
"""
import json
import logging

from langchain_core.tools import tool
from pydantic import BaseModel, Field

from app.config import settings
from app.core.vector_store import get_vector_store
from app.storage.models import Product
from app.storage.database import SessionLocal

log = logging.getLogger(__name__)


# === Tool input schemas ===
class SearchProductsInput(BaseModel):
    keyword: str = Field(..., description="用户的搜索关键词或商品需求描述,如'卧室音箱 预算500'")
    top_k: int = Field(default=8, ge=1, le=12, description="返回商品数量,默认8,最多12")


class GetProductDetailInput(BaseModel):
    product_id: str = Field(..., description="商品 ID,必须是 search_products_by_keyword 返回结果中的 product_id 字段值(UUID 格式,如 '4dcc30c231ae4022b2df4ac37e78b9a5'),不能用序号'1''2'代替")


# === Tool implementations ===
@tool("search_products_by_keyword", args_schema=SearchProductsInput)
def search_products_by_keyword(keyword: str, top_k: int = 8) -> str:
    """根据用户需求/关键词检索商品。返回匹配商品的精简信息(名称、价格、规格、相似度、product_id)。

    使用此工具来查找与用户需求相关的商品。用户通常会描述用途、预算、偏好等。
    当有多个相似商品都符合需求时,应尽量返回更多结果供用户对比选择。
    """
    try:
        vs = get_vector_store()
    except Exception as e:
        log.exception("Vector store init failed: %s", e)
        return json.dumps({"error": "向量库初始化失败", "products": []}, ensure_ascii=False)

    try:
        # similarity_search_with_score returns List[Tuple[Document, float]]
        # Fetch extra candidates so we have room for threshold filtering
        results = vs.similarity_search_with_score(keyword, k=max(top_k * 3, 24))
    except Exception as e:
        log.exception("Similarity search failed: %s", e)
        return json.dumps({"error": f"检索失败: {e}", "products": []}, ensure_ascii=False)

    # Chroma returns cosine distance in [0, 2]; convert to similarity = 1 - distance/2 (range [0, 1])
    # Lowered threshold so that multiple similar products can be returned together
    sim_threshold = 0.40
    products = []
    seen_pids: set[str] = set()

    for doc, distance in results:
        meta = doc.metadata or {}
        # Only return product-type entries
        if meta.get("type") != "product":
            continue
        pid = meta.get("product_id") or ""
        if not pid or pid in seen_pids:
            continue
        similarity = max(0.0, 1.0 - float(distance) / 2.0)
        # Hard threshold filter: reject clearly irrelevant matches
        if similarity < sim_threshold:
            continue
        seen_pids.add(pid)
        products.append(
            {
                "product_id": pid,
                "name": meta.get("name", "未知"),
                "price": meta.get("price", ""),
                "snippet": (doc.page_content or "")[:300],
                "similarity": round(similarity, 4),
            }
        )
        if len(products) >= top_k:
            break

    return json.dumps({"products": products}, ensure_ascii=False)


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
                "stock_status": "充足" if p.stock > 0 else "缺货",
                "merchant_id": p.merchant_id,
            },
            ensure_ascii=False,
        )
    finally:
        db.close()


# Registry exported for chain.py to bind to the LLM
SHOPPING_TOOLS = [search_products_by_keyword, get_product_detail]
