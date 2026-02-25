from datetime import datetime
from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from app.database import Base


class Keyword(Base):
    __tablename__ = "keywords"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False, unique=True)
    alert_price = Column(Float, nullable=False)
    category_id = Column(Integer, nullable=True)  # Mercari 分类ID，可选
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    items = relationship("Item", back_populates="keyword", cascade="all, delete-orphan")
    alert_logs = relationship("AlertLog", back_populates="keyword", cascade="all, delete-orphan")


class Item(Base):
    __tablename__ = "items"

    id = Column(Integer, primary_key=True, index=True)
    mercari_id = Column(String(50), nullable=False, index=True)
    keyword_id = Column(Integer, ForeignKey("keywords.id"), nullable=False)
    title = Column(String(500))
    price = Column(Integer)
    image_url = Column(String)
    product_url = Column(String)
    condition = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    keyword = relationship("Keyword", back_populates="items")
    price_history = relationship("PriceHistory", back_populates="item", cascade="all, delete-orphan")
    alert_logs = relationship("AlertLog", back_populates="item", cascade="all, delete-orphan")


class PriceHistory(Base):
    __tablename__ = "price_history"

    id = Column(Integer, primary_key=True, index=True)
    item_id = Column(Integer, ForeignKey("items.id"), nullable=False)
    price = Column(Float, nullable=False)
    recorded_at = Column(DateTime, default=datetime.utcnow)

    item = relationship("Item", back_populates="price_history")


class AlertLog(Base):
    __tablename__ = "alert_logs"

    id = Column(Integer, primary_key=True, index=True)
    keyword_id = Column(Integer, ForeignKey("keywords.id"), nullable=False)
    item_id = Column(Integer, ForeignKey("items.id"), nullable=False)
    alert_price = Column(Float, nullable=False)
    actual_price = Column(Float, nullable=False)
    email_sent = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    keyword = relationship("Keyword", back_populates="alert_logs")
    item = relationship("Item", back_populates="alert_logs")
