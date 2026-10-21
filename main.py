import os
import random
from typing import Optional
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String, Float, Text
from sqlalchemy.orm import declarative_base, sessionmaker, Session

# ==========================================
# 1. DATABASE SETUP (SQLite ወይም PostgreSQL)
# ==========================================
# Render/Railway ላይ PostgreSQL ከተጠቀሙ DATABASE_URL ይሰራል፣ ከሌለ ግን SQLite ፋይል ይፈጥራል
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./eotc_market.db")
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# ==========================================
# 2. OPTIONAL CLOUDINARY SETUP (ለፎቶ ማከማቻ)
# ==========================================
CLOUDINARY_URL = os.getenv("CLOUDINARY_URL")
use_cloudinary = False
if CLOUDINARY_URL:
    import cloudinary
    import cloudinary.uploader
    use_cloudinary = True

def process_image(base64_or_url: Optional[str]) -> str:
    if not base64_or_url:
        return ""
    if use_cloudinary and base64_or_url.startswith("data:image"):
        try:
            upload_res = cloudinary.uploader.upload(base64_or_url, folder="eotc_market")
            return upload_res.get("secure_url", base64_or_url)
        except Exception:
            return base64_or_url
    return base64_or_url

# ==========================================
# 3. DATABASE MODELS (ቋሚ ሰንጠረዦች)
# ==========================================
class VendorDB(Base):
    __tablename__ = "vendors"
    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(Integer, nullable=True, index=True)
    username = Column(String, index=True)
    store_name = Column(String)
    phone = Column(String)
    telebirr_account = Column(String, default="")
    cbe_account = Column(String, default="")
    abyssinia_account = Column(String, default="")
    id_front_image = Column(Text, default="")
    id_back_image = Column(Text, default="")
    status = Column(String, default="Pending")
    admin_feedback = Column(String, default="")

class ProductDB(Base):
    __tablename__ = "products"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    price = Column(Float)
    category = Column(String, index=True)
    condition = Column(String, default="አዲስ")
    city = Column(String, index=True)
    location = Column(String)
    delivery_fee = Column(Float, default=0.0)
    quantity = Column(String, default="1")
    image = Column(Text, default="")
    image1 = Column(Text, default="")
    image2 = Column(Text, default="")
    image3 = Column(Text, default="")
    seller_username = Column(String, index=True)
    seller_telegram_id = Column(Integer, nullable=True)
    store_name = Column(String, default="EOTC Store")
    # ምድብ-ተኮር ዝርዝሮች
    author = Column(String, default="")
    pub_year = Column(String, default="")
    publisher = Column(String, default="")
    book_sub_category = Column(String, default="መንፈሳዊ")
    size = Column(String, default="M")
    color = Column(String, default="")
    material = Column(String, default="")
    dimension = Column(String, default="")

class OrderDB(Base):
    __tablename__ = "orders"
    id = Column(Integer, primary_key=True, index=True)
    buyer = Column(String)
    buyer_telegram_id = Column(Integer, nullable=True)
    seller_username = Column(String, index=True)
    product_name = Column(String)
    amount = Column(Float)
    payment_method = Column(String)
    tx_ref = Column(String)
    status = Column(String, default="Escrow Under Protection 🛡️")

# ሰንጠረዦቹን በዳታቤዝ ውስጥ መፍጠር
Base.metadata.create_all(bind=engine)

# ==========================================
# 4. FASTAPI APP & CORS
# ==========================================
app = FastAPI(title="EOTC Market High-Speed API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ==========================================
# 5. PYDANTIC SCHEMAS
# ==========================================
class VendorSchema(BaseModel):
    telegram_id: Optional[int] = None
    username: str
    store_name: str
    phone: str
    telebirr_account: Optional[str] = ""
    cbe_account: Optional[str] = ""
    abyssinia_account: Optional[str] = ""
    id_front_image: Optional[str] = ""
    id_back_image: Optional[str] = ""

class BankUpdateSchema(BaseModel):
    username: str
    telebirr_account: Optional[str] = ""
    cbe_account: Optional[str] = ""
    abyssinia_account: Optional[str] = ""

class FeedbackSchema(BaseModel):
    admin_feedback: str
    username: Optional[str] = None

class ProductSchema(BaseModel):
    name: str
    price: float
    category: str
    condition: Optional[str] = "አዲስ"
    city: str
    location: str
    delivery_fee: Optional[float] = 0.0
    quantity: Optional[str] = "1"
    image: Optional[str] = ""
    image1: Optional[str] = ""
    image2: Optional[str] = ""
    image3: Optional[str] = ""
    seller_username: Optional[str] = "admin"
    seller_telegram_id: Optional[int] = None
    store_name: Optional[str] = "EOTC Official Store"
    author: Optional[str] = ""
    pub_year: Optional[str] = ""
    publisher: Optional[str] = ""
    book_sub_category: Optional[str] = "መንፈሳዊ"
    size: Optional[str] = "M"
    color: Optional[str] = ""
    material: Optional[str] = ""
    dimension: Optional[str] = ""

class OrderSchema(BaseModel):
    buyer: str
    buyer_telegram_id: Optional[int] = None
    seller_username: str
    product_name: str
    amount: float
    payment_method: str
    tx_ref: str
    status: Optional[str] = "Escrow Under Protection 🛡️"

# ==========================================
# 6. API ENDPOINTS
# ==========================================
@app.post("/send-otp-username")
def send_otp(data: dict):
    code = str(random.randint(1000, 9999))
    return {"status": "sent", "fallback_code": code}

# --- VENDORS (KYC & BANK) ---
@app.get("/vendors")
def get_vendors(db: Session = Depends(get_db)):
    return db.query(VendorDB).order_by(VendorDB.id.desc()).all()

@app.post("/vendors")
def create_or_update_vendor(v: VendorSchema, db: Session = Depends(get_db)):
    clean_username = v.username.replace("@", "").strip().lower()
    existing = db.query(VendorDB).filter(VendorDB.username == clean_username).first()

    front_img = process_image(v.id_front_image)
    back_img = process_image(v.id_back_image)

    if existing:
        existing.store_name = v.store_name
        existing.phone = v.phone
        existing.telebirr_account = (v.telebirr_account or "").strip()
        existing.cbe_account = (v.cbe_account or "").strip()
        existing.abyssinia_account = (v.abyssinia_account or "").strip()
        if front_img:
            existing.id_front_image = front_img
        if back_img:
            existing.id_back_image = back_img
        existing.status = "Pending"
        existing.admin_feedback = ""
        db.commit()
        db.refresh(existing)
        return existing

    new_vendor = VendorDB(
        telegram_id=v.telegram_id,
        username=clean_username,
        store_name=v.store_name,
        phone=v.phone,
        telebirr_account=(v.telebirr_account or "").strip(),
        cbe_account=(v.cbe_account or "").strip(),
        abyssinia_account=(v.abyssinia_account or "").strip(),
        id_front_image=front_img,
        id_back_image=back_img,
        status="Pending"
    )
    db.add(new_vendor)
    db.commit()
    db.refresh(new_vendor)
    return new_vendor

@app.post("/vendors/update-bank")
def update_vendor_bank(data: BankUpdateSchema, db: Session = Depends(get_db)):
    clean_username = data.username.replace("@", "").strip().lower()
    vendor = db.query(VendorDB).filter(VendorDB.username == clean_username).first()
    if not vendor:
        raise HTTPException(status_code=404, detail="Vendor not found")
    
    vendor.telebirr_account = (data.telebirr_account or "").strip()
    vendor.cbe_account = (data.cbe_account or "").strip()
    vendor.abyssinia_account = (data.abyssinia_account or "").strip()
    vendor.status = "Pending"  # አድሚን እንዲያጸድቀው ወደ Pending ይቀየራል
    db.commit()
    return {"status": "success", "vendor": vendor}

@app.post("/vendors/{vendor_id}/approve")
def approve_vendor(vendor_id: int, db: Session = Depends(get_db)):
    vendor = db.query(VendorDB).filter(VendorDB.id == vendor_id).first()
    if not vendor:
        raise HTTPException(status_code=404, detail="Vendor not found")
    vendor.status = "Approved ✅"
    vendor.admin_feedback = ""
    db.commit()
    return {"status": "approved"}

@app.post("/vendors/{vendor_id}/reject")
def reject_vendor(vendor_id: int, db: Session = Depends(get_db)):
    vendor = db.query(VendorDB).filter(VendorDB.id == vendor_id).first()
    if vendor:
        vendor.status = "Rejected ❌"
        db.commit()
    return {"status": "rejected"}

@app.post("/vendors/{vendor_id}/feedback")
def vendor_feedback(vendor_id: int, data: FeedbackSchema, db: Session = Depends(get_db)):
    vendor = db.query(VendorDB).filter(VendorDB.id == vendor_id).first()
    if not vendor:
        raise HTTPException(status_code=404, detail="Vendor not found")
    vendor.admin_feedback = data.admin_feedback
    vendor.status = "Rejected ❌"  # ፎርሙ እንደገና ተከፍቶ እንዲያስተካክል
    db.commit()
    return {"status": "feedback_saved"}

# --- PRODUCTS ---
@app.get("/products")
def get_products(db: Session = Depends(get_db)):
    return db.query(ProductDB).order_by(ProductDB.id.desc()).all()

@app.post("/products")
def create_product(p: ProductSchema, db: Session = Depends(get_db)):
    main_img = process_image(p.image or p.image1)
    img1 = process_image(p.image1 or main_img)
    img2 = process_image(p.image2)
    img3 = process_image(p.image3)

    new_prod = ProductDB(
        name=p.name,
        price=p.price,
        category=p.category,
        condition=p.condition,
        city=p.city,
        location=p.location,
        delivery_fee=p.delivery_fee,
        quantity=p.quantity,
        image=main_img,
        image1=img1,
        image2=img2,
        image3=img3,
        seller_username=p.seller_username.replace("@", "").strip().lower(),
        seller_telegram_id=p.seller_telegram_id,
        store_name=p.store_name,
        author=p.author,
        pub_year=p.pub_year,
        publisher=p.publisher,
        book_sub_category=p.book_sub_category,
        size=p.size,
        color=p.color,
        material=p.material,
        dimension=p.dimension
    )
    db.add(new_prod)
    db.commit()
    db.refresh(new_prod)
    return new_prod

@app.put("/products/{product_id}")
def update_product(product_id: int, p: ProductSchema, db: Session = Depends(get_db)):
    prod = db.query(ProductDB).filter(ProductDB.id == product_id).first()
    if not prod:
        raise HTTPException(status_code=404, detail="Product not found")

    prod.name = p.name
    prod.price = p.price
    prod.category = p.category
    prod.condition = p.condition
    prod.city = p.city
    prod.location = p.location
    prod.delivery_fee = p.delivery_fee
    prod.author = p.author
    prod.pub_year = p.pub_year
    prod.publisher = p.publisher
    prod.book_sub_category = p.book_sub_category
    prod.size = p.size
    prod.color = p.color
    prod.material = p.material
    prod.dimension = p.dimension

    if p.image:
        prod.image = process_image(p.image)
    if p.image1:
        prod.image1 = process_image(p.image1)
    if p.image2:
        prod.image2 = process_image(p.image2)
    if p.image3:
        prod.image3 = process_image(p.image3)

    db.commit()
    db.refresh(prod)
    return prod

@app.delete("/products/{product_id}")
def delete_product(product_id: int, db: Session = Depends(get_db)):
    prod = db.query(ProductDB).filter(ProductDB.id == product_id).first()
    if prod:
        db.delete(prod)
        db.commit()
    return {"status": "deleted"}

# --- ORDERS ---
@app.get("/orders")
def get_orders(db: Session = Depends(get_db)):
    return db.query(OrderDB).order_by(OrderDB.id.desc()).all()

@app.post("/orders")
def create_order(o: OrderSchema, db: Session = Depends(get_db)):
    new_order = OrderDB(
        buyer=o.buyer,
        buyer_telegram_id=o.buyer_telegram_id,
        seller_username=o.seller_username,
        product_name=o.product_name,
        amount=o.amount,
        payment_method=o.payment_method,
        tx_ref=o.tx_ref,
        status=o.status
    )
    db.add(new_order)
    db.commit()
    db.refresh(new_order)
    return new_order

@app.post("/orders/{order_id}/approve")
def approve_order(order_id: int, db: Session = Depends(get_db)):
    order = db.query(OrderDB).filter(OrderDB.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    order.status = "Released to Vendor ✅"
    db.commit()
    return {"status": "released"}
