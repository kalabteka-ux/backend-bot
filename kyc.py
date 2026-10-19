# ==============================================================
# FOLDER: backend-bot
# FILE: kyc.py
# ==============================================================
from fastapi import APIRouter, Depends, HTTPException, Form, UploadFile, File
from sqlalchemy.orm import Session
from pydantic import BaseModel
from database import get_db
from models import KycVerification, Shop, KycDocType, KycStatus, User
from telegram_auth import verify_telegram_init_data
from bot_service import notify_vendor_kyc_approved

router = APIRouter(prefix="/api/v1/kyc", tags=["KYC"])

@router.post("/submit")
async def submit_vendor_kyc(
    doc_type: KycDocType = Form(...),
    shop_name: str = Form(...),
    full_name: str = Form(...),
    id_number: str = Form(...),
    document_front: UploadFile = File(...),
    tg_user: dict = Depends(verify_telegram_init_data),
    db: Session = Depends(get_db)
):
    """Vendor submits Ethiopian Fayda ID or Passport from Telegram Mini App."""
    user = db.query(User).filter(User.telegram_user_id == tg_user["id"]).first()
    if not user:
        user = User(
            telegram_user_id=tg_user["id"],
            telegram_username=tg_user.get("username"),
            first_name=tg_user.get("first_name", "Vendor"),
            last_name=tg_user.get("last_name")
        )
        db.add(user)
        db.flush()

    # Save mock file path / S3 URL
    file_location = f"uploads/{document_front.filename}"

    kyc = KycVerification(
        vendor_id=user.id,
        doc_type=doc_type,
        id_number=id_number,
        full_name_on_id=full_name,
        document_front_url=file_location,
        status=KycStatus.PENDING
    )
    db.add(kyc)

    if not user.shop:
        shop = Shop(
            vendor_user_id=user.id,
            shop_name=shop_name,
            slug=shop_name.lower().replace(" ", "-"),
            is_active=False # Inactive until Super Admin approves
        )
        db.add(shop)

    db.commit()
    return {"status": "submitted", "message": "KYC pending Super Admin review"}

class ReviewKycPayload(BaseModel):
    action: str  # "APPROVE" or "REJECT"
    reason: str | None = None

@router.post("/{kyc_id}/review")
async def review_kyc(kyc_id: str, payload: ReviewKycPayload, db: Session = Depends(get_db)):
    """Super Admin approves or rejects KYC from the external Next.js dashboard."""
    kyc = db.query(KycVerification).filter(KycVerification.id == kyc_id).first()
    if not kyc:
        raise HTTPException(status_code=404, detail="KYC record not found")

    if payload.action == "APPROVE":
        kyc.status = KycStatus.APPROVED
        shop = db.query(Shop).filter(Shop.vendor_user_id == kyc.vendor_id).first()
        if shop:
            shop.is_active = True
            await notify_vendor_kyc_approved(kyc.vendor.telegram_user_id, shop.shop_name)
    else:
        kyc.status = KycStatus.REJECTED
        kyc.rejection_reason = payload.reason

    db.commit()
    return {"status": "success", "new_status": kyc.status}