# ==============================================================
# FOLDER: backend-bot
# FILE: marketplace.py
# ==============================================================
import uuid
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from database import get_db
from models import Product, Order, User, PaymentGateway, OrderStatus
from telegram_auth import verify_telegram_init_data
from escrow_split_service import calculate_order_split

router = APIRouter(prefix="/api/v1/market", tags=["Marketplace"])

@router.get("/products")
def list_products(db: Session = Depends(get_db)):
    """Returns active products from verified shops."""
    return db.query(Product).filter(Product.is_published == True).all()

class CheckoutItem(BaseModel):
    productId: str
    quantity: int

class CheckoutPayload(BaseModel):
    items: list[CheckoutItem]
    paymentGateway: PaymentGateway
    deliveryAddress: str

@router.post("/orders/checkout")
def create_order(
    payload: CheckoutPayload,
    tg_user: dict = Depends(verify_telegram_init_data),
    db: Session = Depends(get_db)
):
    """Creates order with calculated 1.5% platform commission and 98.5% vendor split."""
    user = db.query(User).filter(User.telegram_user_id == tg_user["id"]).first()
    if not user:
        user = User(
            telegram_user_id=tg_user["id"],
            telegram_username=tg_user.get("username"),
            first_name=tg_user.get("first_name", "Buyer")
        )
        db.add(user)
        db.flush()

    total_gross = Decimal("0.00")
    primary_shop_id = None

    for item in payload.items:
        prod = db.query(Product).filter(Product.id == item.productId).first()
        if prod:
            total_gross += prod.price_etb * item.quantity
            primary_shop_id = prod.shop_id

    if not primary_shop_id or total_gross <= 0:
        raise HTTPException(status_code=400, detail="Invalid items in cart")

    platform_fee, vendor_payout = calculate_order_split(total_gross)
    order_code = f"EOTC-{uuid.uuid4().hex[:6].upper()}"

    order = Order(
        order_code=order_code,
        buyer_id=user.id,
        shop_id=primary_shop_id,
        gross_amount_etb=total_gross,
        platform_commission_etb=platform_fee,
        vendor_net_etb=vendor_payout,
        payment_method=payload.paymentGateway,
        status=OrderStatus.PENDING_PAYMENT,
        delivery_address=payload.deliveryAddress
    )
    db.add(order)
    db.commit()

    # Generate redirect URL to Telebirr or CBE gateway
    payment_url = f"https://gateway.eotc-market.et/pay?order={order_code}&amount={total_gross}&channel={payload.paymentGateway}"

    return {
        "orderCode": order_code,
        "grossAmount": float(total_gross),
        "platformCommission_1_5": float(platform_fee),
        "vendorNet_98_5": float(vendor_payout),
        "paymentUrl": payment_url
    }