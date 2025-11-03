import enum
from sqlalchemy import (
    Column, Integer, String, Boolean, Enum as SQLAlchemyEnum, ForeignKey, Numeric,
    TIMESTAMP, func, Text
)
from sqlalchemy.orm import relationship, declarative_base

Base = declarative_base()

# --------------------------
# ENUMS
# --------------------------
class UserRole(str, enum.Enum):
    admin = "admin"
    seller = "seller"
    customer = "customer"

class OrderStatus(str, enum.Enum):
    pending_validation = "pending_validation"
    approved = "approved"
    shipped = "shipped"
    delivered="delivered"
    cancelled = "cancelled"
    cart="cart"

# --------------------------
# MODELS
# --------------------------
class User(Base):
    __tablename__ = "users"

    user_id = Column(Integer, primary_key=True)
    username = Column(String(255), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, index=True)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(255))
    role = Column(SQLAlchemyEnum(UserRole), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())

    # Relationships 
    customer_info = relationship("CustomerInfo", back_populates="user", uselist=False)
    orders_created = relationship("Order", back_populates="customer", foreign_keys="[Order.user_id]")
    orders_validated = relationship("Order", back_populates="seller", foreign_keys="[Order.seller_id]")
    cart_cache = relationship("CartCache", back_populates="user", cascade="all, delete")

class Category(Base):
    __tablename__ = "categories"

    category_id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)

    # Relationships
    products = relationship("Product", back_populates="category")

class Product(Base):
    __tablename__ = "products"

    product_id = Column(Integer, primary_key=True)
    sku = Column(String(100), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    price = Column(Numeric(10, 2), nullable=False, default=0.00)
    image_url = Column(String(255))
    stock_count = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    category_id = Column(Integer, ForeignKey("categories.category_id"))

    # Relationships
    category = relationship("Category", back_populates="products")
    order_items = relationship("OrderItem", back_populates="product")
    cart_entries = relationship("CartCache", back_populates="product")

class CustomerInfo(Base):
    __tablename__ = "customerinfo"

    customer_info_id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.user_id", ondelete="CASCADE"), unique=True, nullable=False)
    business_name = Column(String(255), nullable=False)
    address = Column(Text)
    rfc = Column(String(13))

    # Relationships
    user = relationship("User", back_populates="customer_info")

class Order(Base):
    __tablename__ = "orders"

    order_id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False, index=True)
    seller_id = Column(Integer, ForeignKey("users.user_id"), index=True)
    status = Column(SQLAlchemyEnum(OrderStatus), nullable=False, default=OrderStatus.cart)
    total_amount = Column(Numeric(12, 2), default=0.00)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    validated_at = Column(TIMESTAMP(timezone=True))

    # Relationships
    customer = relationship("User", back_populates="orders_created", foreign_keys=[user_id])
    seller = relationship("User", back_populates="orders_validated", foreign_keys=[seller_id])
    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")

class OrderItem(Base):
    __tablename__ = "orderitems"

    order_item_id = Column(Integer, primary_key=True)
    order_id = Column(Integer, ForeignKey("orders.order_id", ondelete="CASCADE"), nullable=False, index=True)
    product_id = Column(Integer, ForeignKey("products.product_id"), nullable=False)
    quantity = Column(Integer, nullable=False)
    price_at_purchase = Column(Numeric(10, 2), nullable=False)

    # Relationships
    order = relationship("Order", back_populates="items")
    product = relationship("Product", back_populates="order_items")

# --------------------------
# CART CACHE (nuevo)
# --------------------------
class CartCache(Base):
    __tablename__ = "cartcache"

    cart_cache_id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False, index=True)
    product_id = Column(Integer, ForeignKey("products.product_id"), nullable=False, index=True)
    quantity = Column(Integer, nullable=False, default=1)
    price_at_addition = Column(Numeric(10, 2), nullable=False)
    added_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), onupdate=func.now(), server_default=func.now())

    # Relationships
    user = relationship("User", back_populates="cart_cache")
    product = relationship("Product", back_populates="cart_entries")
