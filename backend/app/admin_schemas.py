from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class StrictAdminInput(BaseModel):
    model_config = ConfigDict(extra="forbid")


class AdminLogin(StrictAdminInput):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class AdminUserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr


class AdminAuthOut(BaseModel):
    user: AdminUserOut
    csrf_token: str


class AdminMeOut(BaseModel):
    user: AdminUserOut


class AdminPlaceholderOut(BaseModel):
    detail: str


class AdminProductImageOut(BaseModel):
    id: int
    product_id: int
    url: str
    alt: str
    sort_order: int
    is_primary: bool


class AdminProductImageUpdate(StrictAdminInput):
    alt: str | None = Field(default=None, max_length=200)
    is_primary: bool | None = None


class AdminMediaOrder(StrictAdminInput):
    ordered_ids: list[int] = Field(min_length=1, max_length=100)

    @field_validator("ordered_ids")
    @classmethod
    def validate_ordered_ids(cls, values: list[int]) -> list[int]:
        if any(value <= 0 for value in values):
            raise ValueError("Los identificadores deben ser positivos")
        if len(values) != len(set(values)):
            raise ValueError("El orden no puede contener identificadores repetidos")
        return values


class AdminProductDocumentOut(BaseModel):
    id: int
    product_id: int
    title: str
    document_type: str
    original_filename: str
    mime_type: str
    size_bytes: int
    is_official: bool
    sort_order: int
    created_at: datetime
    download_url: str


ProductStatus = Literal["active", "inactive"]


class AdminBrandRef(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    slug: str
    is_active: bool


class AdminCategoryRef(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    slug: str
    is_active: bool


class AdminProductCreate(StrictAdminInput):
    sku: str = Field(min_length=1, max_length=60)
    name: str = Field(min_length=1, max_length=200)
    slug: str | None = Field(default=None, max_length=220)
    brand_id: int = Field(gt=0)
    category_id: int = Field(gt=0)
    part_number: str = Field(default="", max_length=80)
    short_description: str = ""
    description: str = ""
    specs: dict[str, Any] = Field(default_factory=dict)
    highlights: list[str] = Field(default_factory=list)
    available_stock: int = Field(default=0, ge=0)
    is_used: bool = False
    status: ProductStatus = "inactive"

    @field_validator("sku", "name")
    @classmethod
    def required_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("El campo no puede estar vacío")
        return value

    @field_validator("slug", mode="before")
    @classmethod
    def empty_slug_is_automatic(cls, value):
        return value.strip() if isinstance(value, str) and value.strip() else None

    @field_validator("part_number", mode="before")
    @classmethod
    def strip_short_text(cls, value):
        return value.strip() if isinstance(value, str) else value

    @field_validator("highlights")
    @classmethod
    def clean_highlights(cls, values: list[str]) -> list[str]:
        cleaned = [value.strip() for value in values if value.strip()]
        if any(len(value) > 500 for value in cleaned):
            raise ValueError("Cada destacado debe tener 500 caracteres o menos")
        return cleaned


class AdminProductUpdate(StrictAdminInput):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    slug: str | None = Field(default=None, min_length=1, max_length=220)
    brand_id: int | None = Field(default=None, gt=0)
    category_id: int | None = Field(default=None, gt=0)
    part_number: str | None = Field(default=None, max_length=80)
    short_description: str | None = None
    description: str | None = None
    specs: dict[str, Any] | None = None
    highlights: list[str] | None = None
    available_stock: int | None = Field(default=None, ge=0)
    is_used: bool | None = None

    @field_validator("name", "slug")
    @classmethod
    def non_empty_text(cls, value: str | None) -> str | None:
        if value is None:
            return value
        value = value.strip()
        if not value:
            raise ValueError("El campo no puede estar vacío")
        return value

    @field_validator("part_number", mode="before")
    @classmethod
    def strip_optional_short_text(cls, value):
        return value.strip() if isinstance(value, str) else value

    @field_validator("highlights")
    @classmethod
    def clean_optional_highlights(cls, values: list[str] | None) -> list[str] | None:
        if values is None:
            return None
        cleaned = [value.strip() for value in values if value.strip()]
        if any(len(value) > 500 for value in cleaned):
            raise ValueError("Cada destacado debe tener 500 caracteres o menos")
        return cleaned


class AdminProductStatusUpdate(StrictAdminInput):
    status: ProductStatus


class AdminProductOut(BaseModel):
    id: int
    sku: str
    name: str
    slug: str
    brand_id: int
    category_id: int
    part_number: str
    short_description: str
    description: str
    specs: dict[str, Any]
    highlights: list
    stock_note: str
    available_stock: int
    stock_type: str
    is_used: bool
    status: ProductStatus
    created_at: datetime
    updated_at: datetime
    brand: AdminBrandRef
    category: AdminCategoryRef
    is_publicly_visible: bool


class AdminProductListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: list[AdminProductOut]


class AdminBrandCreate(StrictAdminInput):
    name: str = Field(min_length=1, max_length=80)
    slug: str | None = Field(default=None, max_length=80)
    description: str = ""
    accent_color: str = Field(default="#1fd7c1", pattern=r"^#[0-9a-fA-F]{6}$")
    is_active: bool = True

    @field_validator("name")
    @classmethod
    def valid_name(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("El nombre no puede estar vacío")
        return value

    @field_validator("slug", mode="before")
    @classmethod
    def empty_slug_is_automatic(cls, value):
        return value.strip() if isinstance(value, str) and value.strip() else None


class AdminBrandUpdate(StrictAdminInput):
    name: str | None = Field(default=None, min_length=1, max_length=80)
    slug: str | None = Field(default=None, min_length=1, max_length=80)
    description: str | None = None
    accent_color: str | None = Field(default=None, pattern=r"^#[0-9a-fA-F]{6}$")

    @field_validator("name", "slug")
    @classmethod
    def non_empty_text(cls, value: str | None) -> str | None:
        if value is None:
            return value
        value = value.strip()
        if not value:
            raise ValueError("El campo no puede estar vacío")
        return value


class AdminActiveUpdate(StrictAdminInput):
    is_active: bool


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


class AdminCategoryCreate(StrictAdminInput):
    name: str = Field(min_length=1, max_length=120)
    slug: str | None = Field(default=None, max_length=120)
    description: str = ""
    is_active: bool = True

    @field_validator("name")
    @classmethod
    def valid_name(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("El nombre no puede estar vacío")
        return value

    @field_validator("slug", mode="before")
    @classmethod
    def empty_slug_is_automatic(cls, value):
        return value.strip() if isinstance(value, str) and value.strip() else None


class AdminCategoryUpdate(StrictAdminInput):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    slug: str | None = Field(default=None, min_length=1, max_length=120)
    description: str | None = None

    @field_validator("name", "slug")
    @classmethod
    def non_empty_text(cls, value: str | None) -> str | None:
        if value is None:
            return value
        value = value.strip()
        if not value:
            raise ValueError("El campo no puede estar vacío")
        return value


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
