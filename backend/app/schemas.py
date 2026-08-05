from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class BrandOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    slug: str
    description: str
    accent_color: str
    logo_url: str


class CategoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    slug: str
    description: str
    icon: str
    image_url: str


class ProductImageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    url: str = Field(validation_alias="resolved_url")
    alt: str
    sort_order: int


class ProductDocumentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    title: str
    document_type: str
    original_filename: str
    mime_type: str
    size_bytes: int
    is_official: bool
    sort_order: int
    download_url: str


class ProductSourceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    source_type: str
    title: str
    url: str
    is_official: bool
    match_scope: str
    notes: str


class ProductFAQOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    question: str
    answer: str
    sort_order: int


class ProductListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    sku: str
    name: str
    slug: str
    short_description: str
    stock_note: str
    price: float | None = None
    currency: str = "PEN"
    available_stock: int
    stock_type: str
    is_used: bool
    brand: BrandOut
    category: CategoryOut
    images: list[ProductImageOut] = []


class ProductDetail(ProductListItem):
    part_number: str
    description: str
    specs: dict
    highlights: list
    created_at: datetime
    documents: list[ProductDocumentOut] = []
    sources: list[ProductSourceOut] = []
    faqs: list[ProductFAQOut] = []


class ProductListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: list[ProductListItem]


class InquiryCreate(BaseModel):
    product_id: int | None = None
    name: str
    email: EmailStr
    phone: str = ""
    company: str = ""
    message: str = ""
    source: str = "contacto"


class InquiryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime


class AdminLogin(BaseModel):
    username: str = Field(min_length=3, max_length=80)
    password: str = Field(min_length=8, max_length=200)


class AdminUserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    username: str
    full_name: str
    role: str


class AdminSessionOut(BaseModel):
    token: str
    expires_at: datetime
    user: AdminUserOut


class AdminProductInput(BaseModel):
    sku: str = Field(min_length=2, max_length=60)
    name: str = Field(min_length=3, max_length=200)
    brand_id: int
    category_id: int
    part_number: str = Field(default="", max_length=80)
    short_description: str = ""
    description: str = ""
    specs: dict = {}
    highlights: list[str] = []
    stock_note: str = Field(default="Disponible bajo cotización", max_length=120)
    price: float | None = Field(default=None, ge=0)
    currency: str = Field(default="PEN", min_length=3, max_length=3)
    available_stock: int = Field(default=0, ge=0)
    stock_type: str = Field(default="serialized", max_length=20)
    is_used: bool = False
    status: str = Field(default="active", pattern="^(active|inactive|draft)$")


class AdminProductPatch(BaseModel):
    sku: str | None = Field(default=None, min_length=2, max_length=60)
    name: str | None = Field(default=None, min_length=3, max_length=200)
    slug: str | None = Field(default=None, min_length=1, max_length=220)
    brand_id: int | None = None
    category_id: int | None = None
    part_number: str | None = Field(default=None, max_length=80)
    short_description: str | None = None
    description: str | None = None
    specs: dict | None = None
    highlights: list[str] | None = None
    stock_note: str | None = Field(default=None, max_length=120)
    price: float | None = Field(default=None, ge=0)
    currency: str | None = Field(default=None, min_length=3, max_length=3)
    available_stock: int | None = Field(default=None, ge=0)
    stock_type: str | None = Field(default=None, max_length=20)
    is_used: bool | None = None
    status: str | None = Field(default=None, pattern="^(active|inactive|draft)$")


class AdminProductOut(ProductDetail):
    status: str
    brand_id: int
    category_id: int
    updated_at: datetime
    is_publicly_visible: bool


class AdminProductListItem(ProductListItem):
    status: str
    brand_id: int
    category_id: int
    updated_at: datetime
    is_publicly_visible: bool


class AdminProductListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: list[AdminProductListItem]


class AdminProductImportRowPreview(BaseModel):
    row_number: int
    sku: str
    name: str
    brand: str
    category: str
    valid: bool
    errors: list[str]
    warnings: list[str]
    raw: dict[str, Any]
    normalized: dict[str, Any]


class AdminProductImportPreview(BaseModel):
    filename: str
    total_rows: int
    valid_rows: int
    invalid_rows: int
    can_import: bool
    rows: list[AdminProductImportRowPreview]


class AdminProductImportCreatedProduct(BaseModel):
    id: int
    sku: str
    name: str
    slug: str


class AdminProductImportResult(BaseModel):
    success: bool
    filename: str
    imported_count: int
    products: list[AdminProductImportCreatedProduct]
    message: str


class AdminProductMediaZipFilePreview(BaseModel):
    path: str
    filename: str
    type: str
    sku: str
    product_id: int | None
    product_name: str
    order: int | None
    size: int
    content_type: str
    valid: bool
    errors: list[str]
    warnings: list[str]


class AdminProductMediaZipProductPreview(BaseModel):
    sku: str
    product_id: int | None
    product_name: str
    images: int
    has_document: bool
    valid: bool
    errors: list[str]


class AdminProductMediaZipPreview(BaseModel):
    filename: str
    total_files: int
    valid_files: int
    invalid_files: int
    related_products: int
    image_count: int
    document_count: int
    can_upload: bool
    files: list[AdminProductMediaZipFilePreview]
    products: list[AdminProductMediaZipProductPreview]


class AdminProductMediaZipAffectedProduct(BaseModel):
    id: int
    sku: str
    name: str
    images_added: int
    documents_added: int


class AdminProductMediaZipResult(BaseModel):
    success: bool
    filename: str
    uploaded_images: int
    uploaded_documents: int
    affected_products: int
    products: list[AdminProductMediaZipAffectedProduct]
    message: str


class AdminActiveUpdate(BaseModel):
    is_active: bool


class AdminStatusUpdate(BaseModel):
    status: str = Field(pattern="^(active|inactive|draft)$")


class AdminBrandInput(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    slug: str | None = Field(default=None, max_length=80)
    description: str = ""
    accent_color: str = Field(default="#0b8c7d", pattern=r"^#[0-9a-fA-F]{6}$")
    is_active: bool = True


class AdminBrandUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=80)
    slug: str | None = Field(default=None, min_length=1, max_length=80)
    description: str | None = None
    accent_color: str | None = Field(default=None, pattern=r"^#[0-9a-fA-F]{6}$")


class AdminBrandOut(BaseModel):
    id: int
    name: str
    slug: str
    description: str
    accent_color: str
    logo_url: str
    is_active: bool
    updated_at: datetime
    product_count: int


class AdminBrandListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: list[AdminBrandOut]


class AdminCategoryInput(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    slug: str | None = Field(default=None, max_length=120)
    description: str = ""
    icon: str = Field(default="▢", max_length=10)
    is_active: bool = True


class AdminCategoryUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    slug: str | None = Field(default=None, min_length=1, max_length=120)
    description: str | None = None
    icon: str | None = Field(default=None, max_length=10)


class AdminCategoryOut(BaseModel):
    id: int
    name: str
    slug: str
    description: str
    icon: str
    image_url: str
    is_active: bool
    updated_at: datetime
    product_count: int


class AdminCategoryListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: list[AdminCategoryOut]


class AdminImageUpdate(BaseModel):
    alt: str | None = Field(default=None, max_length=200)
    is_primary: bool | None = None


class AdminMediaOrder(BaseModel):
    ordered_ids: list[int] = Field(min_length=1, max_length=100)


class AdminImageOut(BaseModel):
    id: int
    product_id: int
    url: str
    alt: str
    sort_order: int
    is_primary: bool


class AdminDocumentOut(BaseModel):
    id: int
    product_id: int
    title: str
    document_type: str
    original_filename: str
    mime_type: str
    size_bytes: int
    is_official: bool
    sort_order: int
    download_url: str
