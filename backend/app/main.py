import os

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.database import Base, engine
from app.auth import ensure_initial_admin
from app.routers import admin, brands, categories, products, inquiries, media
from app.schema_upgrade import apply_additive_schema_upgrades
from app.storage import ensure_bucket

load_dotenv()

Base.metadata.create_all(bind=engine)
apply_additive_schema_upgrades()
ensure_initial_admin()

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

frontend_origins = [
    origin.strip()
    for origin in os.getenv(
        "FRONTEND_ORIGINS",
        os.getenv("FRONTEND_ORIGIN", "http://localhost:5173"),
    ).split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=frontend_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Content-Disposition"],
)

app.include_router(brands.router)
app.include_router(categories.router)
app.include_router(products.router)
app.include_router(inquiries.router)
app.include_router(media.router)
app.include_router(admin.router)


@app.on_event("startup")
def prepare_object_storage():
    # The API remains available if MinIO starts a few seconds later. Uploads
    # retry the bucket check before writing.
    ensure_bucket()


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.get("/api/ready")
def readiness():
    """Report readiness only when the catalog database accepts queries."""
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))
    return {"status": "ready"}
