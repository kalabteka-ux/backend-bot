from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, Column, Integer, String, Text, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
import os

# 1. FastAPI አፕን ማስጀመር
app = FastAPI(title="EOTC Market Backend")

# 2. CORS ማስተካከያ (ከፊት-አንድ / ዳሽቦርድ ጋር እንድገናኝ)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # ሁሉንም የፊት-አንድ ጥያቄዎች እንድቀበል ያደርጋል
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 3. ዳታቤዝ ማዋቀር (Render ላይ PostgreSQL ወይም ሎካል ላይ SQLite እንዲጠቀም)
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./eotc_market.db")

# ለ SQLite እና ሌሎች ዳታቤዞች የሚስማማ የኢንጅን አቀማመጥ
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

# ሠንጠረዦቹን በዳታቤዝ ውስጥ መፍጠር
Base.metadata.create_all(bind=engine)

# የዳታቤዝ ሴሽን (Session) ማግኛ ፉንክሽን
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# 4. መሠረታዊ ራውቶች (Endpoints)
@app.get("/")
def read_root():
    return {"message": "EOTC Market Backend is running successfully!"}

# እቃዎችን ከዳታቤዝ ለማምጣት (Get Products)
@app.get("/products")
def get_products(db: Session = Depends(get_db)):
    products = db.query(ProductModel).all()
    return products

# ከዳሽቦርዱ አዲስ እቃ ለመጫን / ለመጨመር (Create Product)
@app.post("/products")
def create_product(title: str, price: float, description: str = None, image: str = None, db: Session = Depends(get_db)):
    db_product = ProductModel(title=title, price=price, description=description, image=image)
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return {"message": "Product created successfully", "product": db_product}
