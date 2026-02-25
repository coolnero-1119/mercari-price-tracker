import asyncio
import logging
from fastapi import APIRouter, Depends
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
