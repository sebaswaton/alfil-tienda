from fastapi import APIRouter, HTTPException, status

from app.auth.dependencies import CurrentAdmin


router = APIRouter(prefix="/api/admin", tags=["admin-catalog"])


def not_implemented() -> None:
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Endpoint reservado para una etapa posterior",
    )


@router.get("/products/{product_id}/faqs")
def list_product_faqs(product_id: int, _: CurrentAdmin):
    not_implemented()


@router.get("/products/{product_id}/sources")
def list_product_sources(product_id: int, _: CurrentAdmin):
    not_implemented()


@router.get("/inquiries")
def list_inquiries(_: CurrentAdmin):
    not_implemented()


@router.patch("/inquiries/{inquiry_id}/status")
def update_inquiry_status(inquiry_id: int, _: CurrentAdmin):
    not_implemented()
