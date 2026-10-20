import os
import json
import random
import urllib.request
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional

app = FastAPI(title="EOTC Market Username OTP API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

BOT_TOKEN = os.getenv("BOT_TOKEN") or os.getenv("TELEGRAM_BOT_TOKEN") or ""

def send_telegram_message(chat_id: Optional[int], text: str) -> bool:
    if not BOT_TOKEN or not chat_id:
        return False
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        payload = json.dumps({
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "HTML"
        }).encode("utf-8")
        req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=5) as response:
            return response.status == 200
    except Exception as e:
        print("Telegram API Error:", e)
        return False

products_db = [
    {"id": 1, "name": "መጽሐፈ ሰዓታት (ትልቁ)", "price": "650", "category": "መጽሐፍት", "condition": "አዲስ", "location": "አ.አ, ቦሌ", "quantity": "10", "color": "ጥቁር", "badge": "አዲስ", "image": "", "seller_username": "mikael_books", "store_name": "ቅዱስ ሚካኤል መጻሕፍት"},
]
vendors_db = []
orders_db = []

class OtpUsernameRequest(BaseModel):
    username: str
    telegram_id: Optional[int] = None

class VendorIn(BaseModel):
    store_name: str
    username: str
    telegram_id: Optional[int] = None
    phone: str
    account: str
    id_front_image: Optional[str] = ""

class ProductIn(BaseModel):
    name: str
    price: str
    category: Optional[str] = "መጽሐፍት"
    condition: Optional[str] = "አዲስ"
    location: Optional[str] = "አዲስ አበባ"
    quantity: Optional[str] = "1"
    color: Optional[str] = ""
    image: Optional[str] = ""
    seller_username: Optional[str] = "owner"
    store_name: Optional[str] = "EOTC Store"
    seller_telegram_id: Optional[int] = None

class OrderIn(BaseModel):
    buyer: Optional[str] = "buyer"
    buyer_telegram_id: Optional[int] = None
    seller_username: Optional[str] = "owner"
    product_name: str
    amount: str
    payment_method: str
    tx_ref: str

@app.get("/")
def home():
    return {"status": "EOTC Market Username-OTP API Running"}

# በ Telegram Username አማካኝነት OTP ወደ ቦት መላኪያ
@app.post("/send-otp-username")
def send_otp_username(data: OtpUsernameRequest):
    code = str(random.randint(1000, 9999))
    sent = False
    if data.telegram_id:
        msg = (
            f"🔐 <b>የ EOTC Market ማረጋገጫ ኮድ (OTP)</b>\n\n"
            f"የተጠቃሚ ስም (Username): @{data.username}\n"
            f"የእርስዎ ባለ 4-አሃዝ ማረጋገጫ ኮድ፦ <code>{code}</code>\n\n"
            f"እባክዎ ይህንን ኮድ ወደ ሚኒ አፑ ተመልሰው ያስገቡ።"
        )
        sent = send_telegram_message(data.telegram_id, msg)
    return {"ok": True, "sent_via_telegram": sent, "fallback_code": code}

@app.get("/vendors")
def get_vendors():
    return vendors_db

@app.post("/vendors")
def register_vendor(vendor: VendorIn):
    for v in vendors_db:
        if v["username"].lower() == vendor.username.lower():
            v["store_name"] = vendor.store_name
            v["phone"] = vendor.phone
            v["account"] = vendor.account
            if vendor.id_front_image:
                v["id_front_image"] = vendor.id_front_image
            return v

    new_vendor = vendor.dict()
    new_vendor["id"] = len(vendors_db) + 1 + random.randint(100, 999)
    new_vendor["status"] = "Pending"
    vendors_db.insert(0, new_vendor)

    if vendor.telegram_id:
        msg = (
            f"✥ <b>የ KYC ምዝገባ ጥያቄዎ ለአድሚን ደርሷል!</b>\n\n"
            f"🏪 <b>ሱቅ፦</b> {vendor.store_name}\n"
            f"👤 <b>Username፦</b> @{vendor.username}\n"
            f"⏳ <b>ሁኔታ፦</b> በመገምገም ላይ (Pending Review)"
        )
        send_telegram_message(vendor.telegram_id, msg)

    return new_vendor

@app.post("/vendors/{vendor_id}/approve")
def approve_vendor(vendor_id: int):
    for v in vendors_db:
        if v["id"] == vendor_id:
            v["status"] = "Approved ✅"
            if v.get("telegram_id"):
                msg = (
                    f"🎉 <b>እንኳን ደስ አለዎት! ሱቅዎ በአድሚን ጸድቋል!</b>\n\n"
                    f"🏪 <b>ሱቅ፦</b> {v['store_name']}\n"
                    f"✅ አሁን እቃዎችዎን መጫንና መሸጥ ይችላሉ!"
                )
                send_telegram_message(v.get("telegram_id"), msg)
    return {"ok": True}

@app.post("/vendors/{vendor_id}/reject")
def reject_vendor(vendor_id: int):
    global vendors_db
    vendors_db = [v for v in vendors_db if v["id"] != vendor_id]
    return {"ok": True}

@app.get("/products")
def get_products():
    return products_db

@app.post("/products")
def add_product(prod: ProductIn):
    new_prod = prod.dict()
    new_prod["id"] = len(products_db) + 1 + random.randint(1000, 9999)
    new_prod["badge"] = "አዲስ" if prod.condition == "አዲስ" else "ያገለገለ"
    products_db.insert(0, new_prod)
    return new_prod

@app.delete("/products/{product_id}")
def delete_product(product_id: int):
    global products_db
    products_db = [p for p in products_db if p["id"] != product_id]
    return {"ok": True}

@app.get("/orders")
def get_orders():
    return orders_db

@app.post("/orders")
def create_order(order: OrderIn):
    new_order = order.dict()
    new_order["id"] = len(orders_db) + 101 + random.randint(10, 99)
    new_order["status"] = "በሂደት ላይ (Escrow Hold)"
    orders_db.insert(0, new_order)
    if order.buyer_telegram_id:
        send_telegram_message(order.buyer_telegram_id, f"🛡️ የ {order.product_name} ክፍያዎ በ Escrow ተይዟል!")
    return new_order

@app.post("/orders/{order_id}/approve")
def approve_order(order_id: int):
    for o in orders_db:
        if o["id"] == order_id:
            o["status"] = "ተረጋግጧል (Verified ✅)"
    return {"ok": True}

@app.post("/orders/{order_id}/cancel")
def cancel_order(order_id: int):
    for o in orders_db:
        if o["id"] == order_id:
            o["status"] = "ውድቅ ተደርጓል (Cancelled ❌)"
    return {"ok": True}
