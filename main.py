from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional

app = FastAPI(title="EOTC Market API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# የመጀመሪያ የናሙና ዳታዎች
products_db = [
    {"id": 1, "name": "መጽሐፈ ሰዓታት (ትልቁ)", "price": "650", "category": "መጽሐፍት", "badge": "አዲስ"},
    {"id": 2, "name": "የነሐስ የእጅ መስቀል", "price": "1200", "category": "ንዋየ ቅድሳት", "badge": "ተፈላጊ"},
    {"id": 3, "name": "ጥልፍ ነጠላ (ደረጃ 1)", "price": "1850", "category": "አልባሳት", "badge": "ልዩ"},
    {"id": 4, "name": "የእንጨት መቁጠሪያ", "price": "300", "category": "ንዋየ ቅድሳት", "badge": "ቅናሽ"},
]

vendors_db = [
    {"id": 1, "store_name": "ቅዱስ ሚካኤል መጻሕፍት", "username": "mikael_books", "phone": "0911223344", "account": "Telebirr: 0911223344", "status": "Pending"}
]

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
    phone: str
    account: str

class OrderIn(BaseModel):
    id: Optional[int] = None
    buyer: str
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
    return new_vendor

@app.post("/vendors/{vendor_id}/approve")
def approve_vendor(vendor_id: int):
    for v in vendors_db:
        if v["id"] == vendor_id:
            v["status"] = "Approved ✅"
    return {"ok": True}

@app.get("/orders")
def get_orders():
    return orders_db

@app.post("/orders")
def create_order(order: OrderIn):
    new_order = order.dict()
    new_order["id"] = len(orders_db) + 101
    orders_db.insert(0, new_order)
    return new_order

@app.post("/orders/{order_id}/approve")
def approve_order(order_id: int):
    for o in orders_db:
        if o["id"] == order_id:
            o["status"] = "Escrow Released ✅"
    return {"ok": True}
