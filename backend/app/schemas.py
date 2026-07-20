from datetime import datetime

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
