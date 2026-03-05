import asyncio
import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app import crud, schemas
from app.database import get_db

logger = logging.getLogger(__name__)
router = APIRouter(tags=["stats"])


@router.get("/api/price-history/{item_id}", response_model=List[schemas.PriceHistoryOut])
def get_price_history(item_id: int, db: Session = Depends(get_db)):
    return crud.get_price_history(db, item_id)


@router.get("/api/stats", response_model=schemas.StatsOut)
def get_stats(db: Session = Depends(get_db)):
    return crud.get_stats(db)


@router.get("/api/alert-logs", response_model=List[schemas.AlertLogOut])
def get_alert_logs(db: Session = Depends(get_db)):
    return crud.get_alert_logs(db)


@router.post("/api/trigger-crawl", status_code=202)
async def trigger_crawl():
    """手动触发一次爬取（异步后台执行）"""
    from app.crawler import run_crawl
    asyncio.create_task(run_crawl())
    return {"message": "爬取任务已触发，正在后台执行"}


# ─────────────── 屏蔽商品管理 ───────────────

@router.get("/api/blocked-items", tags=["blocked"])
def list_blocked_items(db: Session = Depends(get_db)):
    """查看所有已屏蔽商品列表"""
    items = crud.get_blocked_items(db)
    return [
        {"id": i.id, "mercari_id": i.mercari_id, "title": i.title, "blocked_at": i.blocked_at}
        for i in items
    ]


@router.delete("/api/blocked-items/{mercari_id}", tags=["blocked"])
def unblock_item(mercari_id: str, db: Session = Depends(get_db)):
    """手动解除商品屏蔽，之后该商品的价格预警将重新生效"""
    success = crud.unblock_item(db, mercari_id)
    if not success:
        raise HTTPException(status_code=404, detail="屏蔽记录不存在")
    return {"message": f"商品 {mercari_id} 已解除屏蔽"}

