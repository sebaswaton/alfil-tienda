from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, schemas

router = APIRouter(prefix="/api/inquiries", tags=["inquiries"])


@router.post("", response_model=schemas.InquiryOut, status_code=201)
def create_inquiry(payload: schemas.InquiryCreate, db: Session = Depends(get_db)):
    inquiry = models.Inquiry(**payload.model_dump())
    db.add(inquiry)
    db.commit()
    db.refresh(inquiry)
    return inquiry
