import asyncio
import logging
import random
from datetime import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from app.config import settings

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()
_crawl_task: asyncio.Task = None


def _get_interval_seconds() -> int:
    """根据当前时段返回随机等待秒数"""
    hour = datetime.now().hour
    if settings.NIGHT_START_HOUR <= hour < settings.NIGHT_END_HOUR:
        minutes = random.randint(settings.NIGHT_MIN_INTERVAL, settings.NIGHT_MAX_INTERVAL)
        logger.info(f"夜间模式，下次爬取间隔: {minutes} 分钟")
    else:
        minutes = random.randint(settings.NORMAL_MIN_INTERVAL, settings.NORMAL_MAX_INTERVAL)
        logger.info(f"正常模式，下次爬取间隔: {minutes} 分钟")
    return minutes * 60


async def _crawl_loop():
    """持续循环爬取，每次完成后随机等待"""
    from app.crawler import run_crawl
    while True:
        try:
            await run_crawl()
        except Exception as e:
            logger.error(f"爬取循环发生错误: {e}", exc_info=True)
        wait_seconds = _get_interval_seconds()
        logger.info(f"等待 {wait_seconds} 秒后进行下次爬取...")
        await asyncio.sleep(wait_seconds)


def start_scheduler():
    """启动后台爬取循环"""
    global _crawl_task
    loop = asyncio.get_event_loop()
    _crawl_task = loop.create_task(_crawl_loop())
    logger.info("调度器已启动")


def stop_scheduler():
    """停止后台爬取"""
    global _crawl_task
    if _crawl_task and not _crawl_task.done():
        _crawl_task.cancel()
        logger.info("调度器已停止")
