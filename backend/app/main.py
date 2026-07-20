import os

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import Base, engine
from app.routers import brands, categories, products, inquiries
from app.storage import ensure_bucket

load_dotenv()

Base.metadata.create_all(bind=engine)

app_environment = os.getenv("APP_ENV", "development").strip().lower()
api_docs_enabled = app_environment != "production" or os.getenv(
    "ENABLE_API_DOCS", "false"
).lower() == "true"

app = FastAPI(
    title="Alfil CC — API de catálogo",
    version="1.0.0",
    docs_url="/docs" if api_docs_enabled else None,
    redoc_url="/redoc" if api_docs_enabled else None,
    openapi_url="/openapi.json" if api_docs_enabled else None,
)

frontend_origin = os.getenv("FRONTEND_ORIGIN", "http://localhost:5173")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[frontend_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(brands.router)
app.include_router(categories.router)
app.include_router(products.router)
app.include_router(inquiries.router)


@app.on_event("startup")
def prepare_object_storage():
    # The API remains available if MinIO starts a few seconds later. Uploads
    # retry the bucket check before writing.
    ensure_bucket()


@app.get("/api/health")
def health():
    return {"status": "ok"}
