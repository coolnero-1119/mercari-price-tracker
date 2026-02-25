import logging
from typing import Optional
from sqlalchemy.orm import Session
from app import crud
from app.database import SessionLocal
from app.email_service import send_alert_email
from app.config import settings

logger = logging.getLogger(__name__)


def _mercari_item_to_dict(item) -> Optional[dict]:
    """将 mercapi SearchResultItem 对象转为字典"""
    try:
        # mercapi 0.4+ 使用 id_ 而非 id
        mercari_id = str(item.id_) if hasattr(item, "id_") else str(getattr(item, "id", ""))
        if not mercari_id:
            return None

        price = None
        if hasattr(item, "price") and item.price is not None:
            price = int(item.price)

        image_url = ""
        if hasattr(item, "thumbnails") and item.thumbnails:
            image_url = str(item.thumbnails[0])

        product_url = f"https://jp.mercari.com/item/{mercari_id}"

        condition = ""
        if hasattr(item, "item_condition_id") and item.item_condition_id is not None:
            condition = str(item.item_condition_id)

        return {
            "mercari_id": mercari_id,
            "title": str(item.name) if hasattr(item, "name") else "",
            "price": price,
            "image_url": image_url,
            "product_url": product_url,
            "condition": condition,
        }
    except Exception as e:
        logger.warning(f"解析商品数据失败: {e}")
        return None


async def crawl_keyword(db: Session, keyword_id: int, keyword_name: str, alert_price: float, category_id: Optional[int] = None):
    """爬取单个关键词的商品"""
    try:
        from mercapi import Mercapi
        m = Mercapi()

        cat_info = f" [分类:{category_id}]" if category_id else ""
        logger.info(f"开始爬取关键词: {keyword_name}{cat_info}")

        # 滚动覆盖：先删除该关键词的旧数据
        crud.delete_items_by_keyword(db, keyword_id)

        search_kwargs = {}
        if category_id:
            search_kwargs["categories"] = [category_id]

        results = await m.search(keyword_name, **search_kwargs)
        items = results.items if results and hasattr(results, "items") else []

        # 最多取 MAX_ITEMS_PER_KEYWORD 条
        items = items[: settings.MAX_ITEMS_PER_KEYWORD]
        logger.info(f"关键词 [{keyword_name}] 获取到 {len(items)} 条商品")

        for raw_item in items:
            item_data = _mercari_item_to_dict(raw_item)
            if not item_data:
                continue

            db_item = crud.create_item(db, keyword_id=keyword_id, item_data=item_data)

            # 记录价格历史
            if db_item.price is not None:
                crud.add_price_history(db, db_item.id, db_item.price)

                # 价格预警检查
                if db_item.price <= alert_price:
                    logger.info(
                        f"触发预警! 商品: {db_item.title}, 价格: {db_item.price}, 预警线: {alert_price}"
                    )
                    email_sent = await send_alert_email(
                        keyword_name=keyword_name,
                        alert_price=alert_price,
                        item={
                            "price": db_item.price,
                            "title": db_item.title,
                            "image_url": db_item.image_url,
                            "product_url": db_item.product_url,
                        },
                    )
                    crud.create_alert_log(
                        db,
                        keyword_id=keyword_id,
                        item_id=db_item.id,
                        alert_price=alert_price,
                        actual_price=float(db_item.price),
                        email_sent=email_sent,
                    )

    except Exception as e:
        logger.error(f"爬取关键词 [{keyword_name}] 失败: {e}", exc_info=True)


async def run_crawl():
    """执行一次完整爬取任务"""
    logger.info("========== 开始爬取任务 ==========")
    db: Session = SessionLocal()
    try:
        keywords = crud.get_active_keywords(db)
        if not keywords:
            logger.info("没有启用的关键词，跳过爬取")
            return

        for kw in keywords:
            await crawl_keyword(db, kw.id, kw.name, kw.alert_price, kw.category_id)

        logger.info("========== 爬取任务完成 ==========")
    finally:
        db.close()
