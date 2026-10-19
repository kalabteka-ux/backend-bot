import os
import json
import urllib.request
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional

app = FastAPI(title="EOTC Market API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ከ Render Environment Variable የቦቱን ቶከን ማንበቢያ
BOT_TOKEN = os.getenv("BOT_TOKEN") or os.getenv("TELEGRAM_BOT_TOKEN") or ""

def send_telegram_message(chat_id: Optional[int], text: str):
    """ለተመዝጋቢው በቴሌግራም የማረጋገጫ መልእክት መላኪያ"""
    if not BOT_TOKEN or not chat_id:
        print(f"Skipping Telegram message: BOT_TOKEN or chat_id ({chat_id}) missing.")
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
        print("Telegram sendMessage error:", e)
        return False

products_db = [
    {"id": 1, "name": "መጽሐፈ ሰዓታት (ትልቁ)", "price": "650", "category": "መጽሐፍት", "badge": "አዲስ"},
    {"id": 2, "name": "የነሐስ የእጅ መስቀል", "price": "1200", "category": "ንዋየ ቅድሳት", "badge": "ተፈላጊ"},
    {"id": 3, "name": "ጥልፍ ነጠላ (ደረጃ 1)", "price": "1850", "category": "አልባሳት", "badge": "ልዩ"},
    {"id": 4, "name": "የእንጨት መቁጠሪያ", "price": "300", "category": "ንዋየ ቅድሳት", "badge": "ቅናሽ"},
]

vendors_db = []
orders_db = []

class ProductIn(BaseModel):
    id: Optional[int] = None
    name: str
    price: str
    category: str = "መጽሐፍት"
    badge: str = "አዲስ"

class VendorIn(BaseModel):
    store_name: str
    username: str = "vendor"
    telegram_id: Optional[int] = None
    phone: str
    account: str
    id_type: str = "National ID"
    id_number: str
    id_front_image: str  # Base64 የተደረገ የመታወቂያ ፎቶ

class OrderIn(BaseModel):
    id: Optional[int] = None
    buyer: str
    buyer_telegram_id: Optional[int] = None
    product_name: str
    amount: str
    payment_method: str
    tx_ref: str
    status: str = "Pending Approval"

@app.get("/")
def home():
    return {"status": "EOTC Market Backend is Running!"}

@app.get("/products")
def get_products():
    return products_db

@app.post("/products")
def add_product(prod: ProductIn):
    new_prod = prod.dict()
    new_prod["id"] = len(products_db) + 1
    products_db.insert(0, new_prod)
    return new_prod

@app.get("/vendors")
def get_vendors():
    return vendors_db

@app.post("/vendors")
def register_vendor(vendor: VendorIn):
    new_vendor = vendor.dict()
    new_vendor["id"] = len(vendors_db) + 1
    new_vendor["status"] = "Pending"
    vendors_db.insert(0, new_vendor)

    # ለተመዝጋቢው ወዲያውኑ በቴሌግራም ማረጋገጫ መላክ
    if vendor.telegram_id:
        msg = (
            f"✥ <b>እንኳን ወደ EOTC Market በደህና መጡ!</b>\n\n"
            f"🏪 <b>የሱቅ ስም:</b> {vendor.store_name}\n"
            f"🪪 <b>የመታወቂያ አይነት:</b> {vendor.id_type} ({vendor.id_number})\n"
            f"📋 <b>ሁኔታ:</b> በመገምገም ላይ (Pending Review)\n\n"
            f"የላኩት የመታወቂያ ማረጋገጫ (KYC) በአድሚን ተገምግሞ ሲጸድቅ ወዲያውኑ በዚህ ቦት መልእክት ይደርስዎታል።"
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
                    f"🎉 <b>እንኳን ደስ አለዎት! የሱቅ ምዝገባዎ ጸድቋል!</b>\n\n"
                    f"🏪 <b>ሱቅ:</b> {v['store_name']}\n"
                    f"✅ <b>ሁኔታ:</b> Approved (የተረጋገጠ ነጋዴ)\n\n"
                    f"አሁን ወደ EOTC Market ሚኒ አፕ በመግባት እቃዎችዎን ወደ ገበያው መጫንና መሸጥ ይችላሉ!"
                )
                send_telegram_message(v.get("telegram_id"), msg)
    return {"ok": True}

@app.get("/orders")
def get_orders():
    return orders_db

@app.post("/orders")
def create_order(order: OrderIn):
    new_order = order.dict()
    new_order["id"] = len(orders_db) + 101
    orders_db.insert(0, new_order)

    if order.buyer_telegram_id:
        msg = (
            f"🧾 <b>የክፍያ መረጃዎ ደርሶናል (Escrow Hold)</b>\n\n"
            f"🛍️ <b>እቃ:</b> {order.product_name}\n"
            f"💰 <b>መጠን:</b> {order.amount} ETB ({order.payment_method})\n"
            f"🔢 <b>የክፍያ ቁጥር:</b> {order.tx_ref}\n\n"
            f"ክፍያው እንደተረጋገጠ መልእክት ይደርስዎታል።"
        )
        send_telegram_message(order.buyer_telegram_id, msg)

    return new_order

@app.post("/orders/{order_id}/approve")
def approve_order(order_id: int):
    for o in orders_db:
        if o["id"] == order_id:
            o["status"] = "Escrow Released ✅"
            if o.get("buyer_telegram_id"):
                msg = (
                    f"✅ <b>ክፍያዎ ተረጋግጧል!</b>\n\n"
                    f"ለ <b>{o['product_name']}</b> የፈጸሙት የ {o['amount']} ETB ክፍያ ተረጋግጦ ትዕዛዝዎ ለሻጩ ተላልፏል።"
                )
                send_telegram_message(o.get("buyer_telegram_id"), msg)
    return {"ok": True}
