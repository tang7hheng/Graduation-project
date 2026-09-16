"""FastAPI application entry point."""
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import settings, DATA_DIR
from app.api.v1 import health, chat, sessions, knowledge, merchants, products, orders
from app.storage.database import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Ensure data directories exist
    (DATA_DIR).mkdir(parents=True, exist_ok=True)
    (settings.upload_dir_abs).mkdir(parents=True, exist_ok=True)
    (settings.chroma_dir_abs).mkdir(parents=True, exist_ok=True)
    # Create database tables
    init_db()
    yield


app = FastAPI(
    title="RAG Customer Service",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
api_prefix = "/api/v1"
app.include_router(health.router, prefix=api_prefix)
app.include_router(chat.router, prefix=api_prefix)
app.include_router(sessions.router, prefix=api_prefix)
app.include_router(knowledge.router, prefix=api_prefix)
app.include_router(merchants.router, prefix=api_prefix)
app.include_router(products.router, prefix=api_prefix)
app.include_router(orders.router, prefix=api_prefix)


# Serve product images as static files
_images_dir = Path(__file__).resolve().parent.parent.parent / "images"
if _images_dir.is_dir():
    app.mount("/images", StaticFiles(directory=str(_images_dir)), name="images")


@app.get("/")
def root():
    return {"name": "RAG Customer Service", "docs": "/docs", "version": "0.1.0"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=settings.app_host, port=settings.app_port, reload=True)
