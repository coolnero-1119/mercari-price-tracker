from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel


# ─────────────── Keyword ───────────────

class KeywordCreate(BaseModel):
    name: str
    alert_price: float
    is_active: bool = True


class KeywordUpdate(BaseModel):
    name: Optional[str] = None
    alert_price: Optional[float] = None
    is_active: Optional[bool] = None


class KeywordOut(BaseModel):
    id: int
    name: str
    alert_price: float
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ─────────────── Item ───────────────

class ItemOut(BaseModel):
    id: int
    mercari_id: str
    keyword_id: int
    title: Optional[str]
    price: Optional[int]
    image_url: Optional[str]
    product_url: Optional[str]
    condition: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ─────────────── PriceHistory ───────────────

class PriceHistoryOut(BaseModel):
    id: int
    item_id: int
    price: float
    recorded_at: datetime

    class Config:
        from_attributes = True


# ─────────────── AlertLog ───────────────

class AlertLogOut(BaseModel):
    id: int
    keyword_id: int
    item_id: int
    alert_price: float
    actual_price: float
    email_sent: bool
    created_at: datetime

    class Config:
        from_attributes = True


# ─────────────── Stats ───────────────

class StatsOut(BaseModel):
    total_keywords: int
    active_keywords: int
    total_items: int
    total_alerts: int
    last_crawl_time: Optional[datetime]
