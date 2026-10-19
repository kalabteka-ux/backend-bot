# ==============================================================
# FOLDER: backend-bot
# FILE: models.py
# ==============================================================
import enum
import uuid
from decimal import Decimal
from sqlalchemy import (
    Column, String, BigInteger, Boolean, Numeric, ForeignKey,
    DateTime, Text, Enum, Integer
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base

class UserRole(str, enum.Enum):
    BUYER = "BUYER"
    VENDOR = "VENDOR"
    SUPER_ADMIN = "SUPER_ADMIN"

class KycStatus(str, enum.Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"

class KycDocType(str, enum.Enum):
    FAYDA_ID = "FAYDA_ID"        # Ethiopian National Digital ID
    PASSPORT = "PASSPORT"

class OrderStatus(str, enum.Enum):
    PENDING_PAYMENT = "PENDING_PAYMENT"
    ESCROW_LOCKED = "ESCROW_LOCKED"
    DISPATCHED = "DISPATCHED"
    DELIVERED = "DELIVERED"
    REFUNDED = "REFUNDED"

class PaymentGateway(str, enum.Enum):
    TELEBIRR = "TELEBIRR"
    CBE_BIRR = "CBE_BIRR"

class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    telegram_user_id = Column(BigInteger, unique=True, nullable=False, index=True)
    telegram_username = Column(String(120), nullable=True)
    first_name = Column(String(120), nullable=False)
    last_name = Column(String(120), nullable=True)
    role = Column(Enum(UserRole), default=UserRole.BUYER)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    shop = relationship("Shop", back_populates="vendor", uselist=False)
    kyc_records = relationship("KycVerification", back_populates="vendor")
    wallet = relationship("Wallet", back_populates="vendor", uselist=False)

class Shop(Base):
    __tablename__ = "shops"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    vendor_user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    shop_name = Column(String(180), nullable=False)
    slug = Column(String(200), unique=True, nullable=False)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=False)  # Activated once Super Admin approves KYC
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    vendor = relationship("User", back_populates="shop")
    products = relationship("Product", back_populates="shop")

class KycVerification(Base):
    __tablename__ = "kyc_verifications"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    vendor_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    doc_type = Column(Enum(KycDocType), nullable=False)
    id_number = Column(String(100), nullable=False)
    full_name_on_id = Column(String(180), nullable=False)
    document_front_url = Column(Text, nullable=False)
    status = Column(Enum(KycStatus), default=KycStatus.PENDING, index=True)
    rejection_reason = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    vendor = relationship("User", back_populates="kyc_records")

class Product(Base):
    __tablename__ = "products"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    shop_id = Column(String(36), ForeignKey("shops.id"), nullable=False)
    title = Column(String(255), nullable=False)
    amharic_title = Column(String(255), nullable=True)
    category = Column(String(100), nullable=False)
    price_etb = Column(Numeric(18, 2), nullable=False)
    stock_quantity = Column(Integer, default=1)
    is_published = Column(Boolean, default=True)

    shop = relationship("Shop", back_populates="products")

class Order(Base):
    __tablename__ = "orders"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    order_code = Column(String(32), unique=True, nullable=False, index=True)
    buyer_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    shop_id = Column(String(36), ForeignKey("shops.id"), nullable=False)
    gross_amount_etb = Column(Numeric(18, 2), nullable=False)
    
    # 1.5% Commission and 98.5% Vendor Split
    commission_rate = Column(Numeric(6, 4), default=Decimal("0.0150"))
    platform_commission_etb = Column(Numeric(18, 2), nullable=False)
    vendor_net_etb = Column(Numeric(18, 2), nullable=False)

    payment_method = Column(Enum(PaymentGateway), nullable=False)
    payment_reference = Column(String(128), unique=True, nullable=True)
    status = Column(Enum(OrderStatus), default=OrderStatus.PENDING_PAYMENT, index=True)
    delivery_address = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    shop = relationship("Shop")

class Wallet(Base):
    __tablename__ = "wallets"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    vendor_id = Column(String(36), ForeignKey("users.id"), unique=True, nullable=False)
    available_balance_etb = Column(Numeric(18, 2), default=Decimal("0.00"))
    escrow_locked_etb = Column(Numeric(18, 2), default=Decimal("0.00"))
    payout_account_type = Column(Enum(PaymentGateway), default=PaymentGateway.TELEBIRR)
    payout_account_number = Column(String(64), nullable=False)

    vendor = relationship("User", back_populates="wallet")

class PlatformMasterWallet(Base):
    __tablename__ = "platform_master_wallet"

    id = Column(Integer, primary_key=True, default=1)
    total_commission_revenue_etb = Column(Numeric(18, 2), default=Decimal("0.00"))
    total_lifetime_gmv_etb = Column(Numeric(18, 2), default=Decimal("0.00"))
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())