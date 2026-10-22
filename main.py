from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, Column, Integer, String, Text, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from pydantic import BaseModel
import os

# 1. FastAPI አፕን ማስጀመር
app = FastAPI(title="EOTC Market Backend")

# 2. CORS ማስተካከያ (Vercel እና ሌሎች አፕሊኬሽኖች እንድገናኙ ሙሉ ፈቃድ የሚሰጥ)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # ከየትኛውም ቦታ የሚመጣ ጥያቄ እንድቀበል ያደርጋል
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 3. ዳታቤዝ ማዋቀር (Render ላይ PostgreSQL ወይም ሎካል ላይ SQLite እንዲጠቀም)
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./eotc_market.db")

connect_args = {"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# የዳታቤዝ ሞዴል (Products / እቃዎች)
class ProductModel(Base):
    __tablename__ = "products"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    price = Column(Float)
    description = Column(Text, nullable=True)
    image = Column(String, nullable=True)

Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# የ Pydantic ሞዴል (ከዳሽቦርዱ የሚመጣውን ጃሰን ዴታ (JSON) በአግባቡ ለመቀበል - ይህ የ 422 ስህተትን ያስወግዳል)
class ProductCreate(BaseModel):
    title: str
    price: float
    description: str | None = None
    image: str | None = None

# መሠረታዊ ራውቶች
@app.get("/")
def read_root():
    return {"message": "EOTC Market Backend is running successfully!"}

@app.get("/products")
def get_products(db: Session = Depends(get_db)):
    products = db.query(ProductModel).all()
    return products

# እቃዎችን ከዳሽቦርዱ ለመቀበል እና በዳታቤዝ ውስጥ ለማስቀመጥ
@app.post("/products")
def create_product(product: ProductCreate, db: Session = Depends(get_db)):
    db_product = ProductModel(
        title=product.title,
        price=product.price,
        description=product.description,
        image=product.image
    )
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return {"message": "Product created successfully", "product": db_product}
