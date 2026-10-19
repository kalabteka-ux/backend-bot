# ==============================================================
# FOLDER: backend-bot
# FILE: payments.py
# ==============================================================
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from database import get_db
from models import Order
from escrow_split_service import lock_funds_in_escrow
from bot_service import notify_vendor_order_received

router = APIRouter(prefix="/api/v1/payments", tags=["Payments"])

@router.post("/telebirr/webhook")
async def telebirr_webhook(request: Request, db: Session = Depends(get_db)):
    """Webhook invoked by Telebirr after customer completes in-app or USSD payment."""
    data = await request.json()
    out_trade_no = data.get("outTradeNo")
    trade_status = data.get("tradeStatus") # e.g. "Completed"
    trans_no = data.get("transactionNo")

    if trade_status == "Completed":
        order = db.query(Order).filter(Order.order_code == out_trade_no).first()
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")

        lock_funds_in_escrow(db, order.id, trans_no)

        # Notify vendor over Telegram
        await notify_vendor_order_received(
            telegram_user_id=order.shop.vendor.telegram_user_id,
            order_code=order.order_code,
            gross=float(order.gross_amount_etb),
            net_payout=float(order.vendor_net_etb)
        )
        return {"code": 0, "message": "Telebirr escrow locked"}

    return {"code": 1, "message": "Payment pending or failed"}

@router.post("/cbe/webhook")
async def cbe_webhook(request: Request, db: Session = Depends(get_db)):
    """Webhook invoked by Commercial Bank of Ethiopia (CBE Birr)."""
    data = await request.json()
    order_ref = data.get("billReference")
    cbe_txn_id = data.get("cbeTransactionId")
    status = data.get("status")

    if status == "SUCCESS":
        order = db.query(Order).filter(Order.order_code == order_ref).first()
        if order:
            lock_funds_in_escrow(db, order.id, cbe_txn_id)
            await notify_vendor_order_received(
                telegram_user_id=order.shop.vendor.telegram_user_id,
                order_code=order.order_code,
                gross=float(order.gross_amount_etb),
                net_payout=float(order.vendor_net_etb)
            )
            return {"status": "ACK"}

    return {"status": "REJECTED"}