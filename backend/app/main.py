import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import brands, categories, products, inquiries
from app.routers.admin import auth as admin_auth
from app.routers.admin import brands as admin_brands
from app.routers.admin import categories as admin_categories
from app.routers.admin import media as admin_media
from app.routers.admin import placeholders as admin_placeholders
from app.routers.admin import products as admin_products
from app.storage import ensure_bucket

load_dotenv()

@asynccontextmanager
async def lifespan(_: FastAPI):
    # The API remains available if MinIO starts a few seconds later. Uploads
    # retry the bucket check before writing.
    ensure_bucket()
    yield


app = FastAPI(title="Alfil CC — API de catálogo", version="1.0.0", lifespan=lifespan)

frontend_origin = os.getenv("FRONTEND_ORIGIN", "http://localhost:5173")
admin_frontend_origin = os.getenv("ADMIN_FRONTEND_ORIGIN", "http://localhost:5174")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[frontend_origin, admin_frontend_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(brands.router)
app.include_router(categories.router)
app.include_router(products.router)
app.include_router(inquiries.router)
app.include_router(admin_auth.router)
app.include_router(admin_products.router)
app.include_router(admin_brands.router)
app.include_router(admin_categories.router)
app.include_router(admin_media.router)
app.include_router(admin_placeholders.router)


@app.get("/api/health")
def health():
    return {"status": "ok"}
