import os
import json
import random
import urllib.request
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional

app = FastAPI(title="EOTC Market Production API")

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
    {"id": 1, "name": "መጽሐፈ ሰዓታት (ትልቁ)", "price": "650", "category": "መጽሐፍት", "condition": "አዲስ", "location": "አ.አ, ቦሌ", "quantity": "10", "color": "ጥቁር", "badge": "አዲስ", "image": "", "seller_username": "mikael_books"},
    {"id": 2, "name": "የነሐስ የእጅ መስቀል", "price": "1200", "category": "ንዋየ ቅድሳት", "condition": "አዲስ", "location": "አ.አ, መገናኛ", "quantity": "5", "color": "ወርቃማ", "badge": "ተፈላጊ", "image": "", "seller_username": "mikael_books"},
    {"id": 3, "name": "ጥልፍ ነጠላ (ደረጃ 1)", "price": "1850", "category": "አልባሳት", "condition": "አዲስ", "location": "አ.አ, ፒያሳ", "quantity": "8", "color": "ነጭ", "badge": "ልዩ", "image": "", "seller_username": "mikael_books"},
]

vendors_db = []
orders_db = []
otp_store = {}

class OtpRequest(BaseModel):
    phone: str
    telegram_id: Optional[int] = None
    username: Optional[str] = "user"

class VendorIn(BaseModel):
    store_name: str
    username: Optional[str] = "vendor"
    telegram_id: Optional[int] = None
    phone: str
    account: str
    id_front_image: str
    otp_code: Optional[str] = ""

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
    seller_telegram_id: Optional[int] = None

class OrderIn(BaseModel):
    buyer: Optional[str] = "buyer"
    buyer_telegram_id: Optional[int] = None
    seller_username: Optional[str] = ""
    product_name: str
    amount: str
    payment_method: str
    tx_ref: str

@app.get("/")
def home():
    return {"status": "EOTC Market Live API Running"}

# 1. የቴሌግራም OTP መላኪያ
@app.post("/send-otp")
def send_otp(data: OtpRequest):
    code = str(random.randint(1000, 9999))
    key = str(data.telegram_id) if data.telegram_id else data.phone
    otp_store[key] = code

    sent = False
    if data.telegram_id:
        msg = (
            f"🔐 <b>የ EOTC Market ማረጋገጫ ኮድ (OTP)</b>\n\n"
            f"የእርስዎ ባለ 4-አሃዝ ማረጋገጫ ኮድ፦ <code>{code}</code>\n"
            f"📞 ስልክ፦ {data.phone}\n\n"
            f"እባክዎ ይህንን ኮድ ወደ ሚኒ አፑ ተመልሰው ያስገቡ።"
        )
        sent = send_telegram_message(data.telegram_id, msg)

    return {"ok": True, "sent_via_telegram": sent, "fallback_code": code}

# 2. የነጋዴዎች KYC ምዝገባና ማጽደቂያ
@app.get("/vendors")
def get_vendors():
    return vendors_db

@app.post("/vendors")
def register_vendor(vendor: VendorIn):
    # የቴሌግራም ID ካለው በነባሩ ላይ ማዘመን ወይም አዲስ መፍጠር
    new_vendor = vendor.dict()
    new_vendor["id"] = len(vendors_db) + 1
    new_vendor["status"] = "Pending"
    vendors_db.insert(0, new_vendor)

    if vendor.telegram_id:
        msg = (
            f"✥ <b>የ KYC ምዝገባዎ ደርሶናል!</b>\n\n"
            f"🏪 <b>ሱቅ፦</b> {vendor.store_name}\n"
            f"📞 <b>ስልክ፦</b> {vendor.phone}\n"
            f"⏳ <b>ሁኔታ፦</b> በአድሚን በመገምገም ላይ (Pending Review)\n\n"
            f"መታወቂያዎ ተረጋግጦ ሲጸድቅ ወዲያውኑ በዚህ ቦት መልእክት ይደርስዎታል።"
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
                    f"🎉 <b>እንኳን ደስ አለዎት! ሱቅዎ ጸድቋል!</b>\n\n"
                    f"🏪 <b>የሱቅ ስም፦</b> {v['store_name']}\n"
                    f"✅ <b>ሁኔታ፦</b> የተረጋገጠ ነጋዴ (Verified Vendor)\n\n"
                    f"አሁን ወደ EOTC Market ሚኒ አፕ በመግባት እቃዎችዎን ወደ ገበያ መጫንና መሸጥ ይችላሉ!"
                )
                send_telegram_message(v.get("telegram_id"), msg)
    return {"ok": True}

# 3. የእቃዎች መጫኛና ማሳያ
@app.get("/products")
def get_products():
    return products_db

@app.post("/products")
def add_product(prod: ProductIn):
    new_prod = prod.dict()
    new_prod["id"] = len(products_db) + 1
    new_prod["badge"] = "አዲስ" if prod.condition == "አዲስ" else "ያገለገለ"
    products_db.insert(0, new_prod)
    return new_prod

# 4. የክፍያ (Escrow) እና ትዕዛዝ መቆጣጠሪያ
@app.get("/orders")
def get_orders():
    return orders_db

@app.post("/orders")
def create_order(order: OrderIn):
    new_order = order.dict()
    new_order["id"] = len(orders_db) + 101
    new_order["status"] = "በሂደት ላይ (Escrow Hold)"
    orders_db.insert(0, new_order)

    if order.buyer_telegram_id:
        msg = (
            f"🛡️ <b>የክፍያ መረጃዎ በ Escrow ተይዟል!</b>\n\n"
            f"🛍️ <b>እቃ፦</b> {order.product_name}\n"
            f"💰 <b>መጠን፦</b> {order.amount} ETB ({order.payment_method})\n"
            f"🔢 <b>የክፍያ ቁጥር (Ref)፦</b> <code>{order.tx_ref}</code>\n"
            f"⏳ <b>ሁኔታ፦</b> በሂደት ላይ (Waiting Admin Verification)\n\n"
            f"ክፍያው በአድሚን እንደተረጋገጠ ወዲያውኑ መልእክት ይደርስዎታል።"
        )
        send_telegram_message(order.buyer_telegram_id, msg)

    return new_order

@app.post("/orders/{order_id}/approve")
def approve_order(order_id: int):
    for o in orders_db:
        if o["id"] == order_id:
            o["status"] = "ተረጋግጧል (Verified ✅)"
            if o.get("buyer_telegram_id"):
                msg = (
                    f"✅ <b>ክፍያዎ ተረጋግጧል!</b>\n\n"
                    f"🛍️ <b>እቃ፦</b> {o['product_name']}\n"
                    f"💰 <b>የተከፈለ፦</b> {o['amount']} ETB\n"
                    f"📦 <b>ሁኔታ፦</b> ተረጋግጧል (ትዕዛዝዎ ለሻጩ ተላልፏል)"
                )
                send_telegram_message(o.get("buyer_telegram_id"), msg)
    return {"ok": True}
