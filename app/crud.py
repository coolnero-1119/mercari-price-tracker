from datetime import datetime
from typing import List, Optional
from sqlalchemy.orm import Session
from app import models, schemas


# ─────────────── Keywords ───────────────

def get_keywords(db: Session) -> List[models.Keyword]:
    return db.query(models.Keyword).all()


def get_keyword(db: Session, keyword_id: int) -> Optional[models.Keyword]:
    return db.query(models.Keyword).filter(models.Keyword.id == keyword_id).first()


def get_active_keywords(db: Session) -> List[models.Keyword]:
    return db.query(models.Keyword).filter(models.Keyword.is_active == True).all()


def create_keyword(db: Session, data: schemas.KeywordCreate) -> models.Keyword:
    kw = models.Keyword(**data.model_dump())
    db.add(kw)
    db.commit()
    db.refresh(kw)
    return kw


def update_keyword(db: Session, keyword_id: int, data: schemas.KeywordUpdate) -> Optional[models.Keyword]:
    kw = get_keyword(db, keyword_id)
    if not kw:
        return None
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(kw, field, value)
    kw.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(kw)
    return kw


def delete_keyword(db: Session, keyword_id: int) -> bool:
    kw = get_keyword(db, keyword_id)
    if not kw:
        return False
    db.delete(kw)
    db.commit()
    return True


# ─────────────── Items ───────────────

def get_items(db: Session, keyword_id: Optional[int] = None) -> List[models.Item]:
    q = db.query(models.Item)
    if keyword_id:
        q = q.filter(models.Item.keyword_id == keyword_id)
    return q.all()


def get_item(db: Session, item_id: int) -> Optional[models.Item]:
    return db.query(models.Item).filter(models.Item.id == item_id).first()


def get_item_by_mercari_id(db: Session, mercari_id: str) -> Optional[models.Item]:
    return db.query(models.Item).filter(models.Item.mercari_id == mercari_id).first()


def delete_items_by_keyword(db: Session, keyword_id: int):
    """滚动覆盖：删除指定关键词的所有商品"""
    db.query(models.Item).filter(models.Item.keyword_id == keyword_id).delete()
    db.commit()


def create_item(db: Session, keyword_id: int, item_data: dict) -> models.Item:
    item = models.Item(keyword_id=keyword_id, **item_data)
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


# ─────────────── PriceHistory ───────────────

def add_price_history(db: Session, item_id: int, price: float) -> models.PriceHistory:
    ph = models.PriceHistory(item_id=item_id, price=price)
    db.add(ph)
    db.commit()
    db.refresh(ph)
    return ph


def get_price_history(db: Session, item_id: int) -> List[models.PriceHistory]:
    return (
        db.query(models.PriceHistory)
        .filter(models.PriceHistory.item_id == item_id)
        .order_by(models.PriceHistory.recorded_at.desc())
        .all()
    )


# ─────────────── AlertLog ───────────────

def create_alert_log(
    db: Session,
    keyword_id: int,
    item_id: int,
    alert_price: float,
    actual_price: float,
    email_sent: bool,
) -> models.AlertLog:
    log = models.AlertLog(
        keyword_id=keyword_id,
        item_id=item_id,
        alert_price=alert_price,
        actual_price=actual_price,
        email_sent=email_sent,
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    return log


def get_alert_logs(db: Session) -> List[models.AlertLog]:
    return db.query(models.AlertLog).order_by(models.AlertLog.created_at.desc()).all()


# ─────────────── Stats ───────────────

def get_stats(db: Session) -> dict:
    total_keywords = db.query(models.Keyword).count()
    active_keywords = db.query(models.Keyword).filter(models.Keyword.is_active == True).count()
    total_items = db.query(models.Item).count()
    total_alerts = db.query(models.AlertLog).count()
    last_item = db.query(models.Item).order_by(models.Item.updated_at.desc()).first()
    last_crawl_time = last_item.updated_at if last_item else None
    return {
        "total_keywords": total_keywords,
        "active_keywords": active_keywords,
        "total_items": total_items,
        "total_alerts": total_alerts,
        "last_crawl_time": last_crawl_time,
    }
