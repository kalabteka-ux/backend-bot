# ==============================================================
# FOLDER: backend-bot
# FILE: escrow_split_service.py
# ==============================================================
from decimal import Decimal, ROUND_HALF_UP
from sqlalchemy.orm import Session
from fastapi import HTTPException
from models import Order, Wallet, PlatformMasterWallet, OrderStatus

COMMISSION_RATE = Decimal("0.015")  # Flat 1.5% EOTC Market Platform Fee

def calculate_order_split(gross_amount: Decimal) -> tuple[Decimal, Decimal]:
    """Calculates the 1.5% platform cut and 98.5% seller payout in ETB."""
    platform_cut = (gross_amount * COMMISSION_RATE).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    seller_payout = gross_amount - platform_cut
    return platform_cut, seller_payout

def lock_funds_in_escrow(db: Session, order_id: str, payment_ref: str):
    """Locks 100% of order funds in escrow upon Telebirr/CBE callback."""
    order = db.query(Order).filter(Order.id == order_id).with_for_update().first()
    if not order or order.status != OrderStatus.PENDING_PAYMENT:
        raise HTTPException(status_code=400, detail="Invalid order state for escrow locking")

    order.payment_reference = payment_ref
    order.status = OrderStatus.ESCROW_LOCKED

    vendor_wallet = db.query(Wallet).filter(Wallet.vendor_id == order.shop.vendor_user_id).first()
    if vendor_wallet:
        vendor_wallet.escrow_locked_etb += order.vendor_net_etb

    db.commit()

def release_escrow_upon_delivery(db: Session, order_id: str):
    """
    Atomically splits the escrow balance:
    - 1.5% credited to the Platform Master Wallet (Admin revenue)
    - 98.5% credited to the Seller's Available Wallet for withdrawal
    """
    with db.begin():
        order = db.query(Order).filter(Order.id == order_id).with_for_update().first()
        if not order or order.status != OrderStatus.ESCROW_LOCKED:
            raise HTTPException(status_code=400, detail="Order is not in ESCROW_LOCKED status")

        # 1. Update Platform Master Wallet (+1.5%)
        master = db.query(PlatformMasterWallet).filter_by(id=1).with_for_update().first()
        if not master:
            master = PlatformMasterWallet(id=1)
            db.add(master)
        master.total_commission_revenue_etb += order.platform_commission_etb
        master.total_lifetime_gmv_etb += order.gross_amount_etb

        # 2. Release 98.5% to Seller
        vendor_wallet = db.query(Wallet).filter(Wallet.vendor_id == order.shop.vendor_user_id).with_for_update().first()
        if not vendor_wallet:
            raise HTTPException(status_code=500, detail="Vendor wallet not found")
        vendor_wallet.available_balance_etb += order.vendor_net_etb
        vendor_wallet.escrow_locked_etb -= order.vendor_net_etb

        # 3. Transition Status
        order.status = OrderStatus.DELIVERED