"""Global application configuration loaded from .env."""
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


# Backend root: backend/  (this file is at backend/app/config.py)
BACKEND_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = BACKEND_ROOT / "data"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BACKEND_ROOT / ".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # === LLM ===
    # 密钥必须通过 backend/.env 的 DEEPSEEK_API_KEY 配置,不要在源码中硬编码
    deepseek_api_key: str = ""
    deepseek_base_url: str = "https://api.deepseek.com"
    deepseek_model: str = "deepseek-flash"
    llm_temperature: float = 0.3
    llm_max_tokens: int = 2048

    # === Embedding ===
    embedding_model: str = "BAAI/bge-small-zh-v1.5"
    hf_endpoint: str = "https://hf-mirror.com"

    # === Vector store ===
    chroma_persist_dir: str = "./data/chroma"
    chroma_collection: str = "kb_default"

    # === Retrieval ===
    # Cosine-similarity threshold used by the retrieval tools (products + knowledge base).
    # 0.40 keeps product recall broad enough to return multiple comparable items.
    retrieval_similarity_threshold: float = 0.40
    # 向量召回后送入后续精排/过滤的候选池上限(越大召回越全但越慢)
    retrieval_candidate_k: int = 40

    # === Reranker (cross-encoder 精排,显著提升商品推荐准确率) ===
    # 加载失败会自动降级为纯向量排序,不影响可用性
    enable_reranker: bool = True
    reranker_model: str = "BAAI/bge-reranker-base"

    # === Memory ===
    memory_buffer_size: int = 10
    memory_summary_trigger: int = 20

    # === Storage ===
    sqlite_db_path: str = "./data/app.db"
    upload_dir: str = "./data/uploads"

    # === App ===
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    cors_origins: str = "http://localhost:5173"

    @property
    def chroma_dir_abs(self) -> Path:
        p = Path(self.chroma_persist_dir)
        return p if p.is_absolute() else BACKEND_ROOT / p

    @property
    def sqlite_db_abs(self) -> Path:
        p = Path(self.sqlite_db_path)
        return p if p.is_absolute() else BACKEND_ROOT / p

    @property
    def upload_dir_abs(self) -> Path:
        p = Path(self.upload_dir)
        return p if p.is_absolute() else BACKEND_ROOT / p

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


settings = Settings()
