import inspect
import logging
from typing import Any, Iterable, Optional
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

        seller = ""
        try:
            if hasattr(item, "seller") and item.seller:
                if hasattr(item.seller, "name"):
                    seller = str(item.seller.name)
                elif hasattr(item.seller, "id"):
                    seller = str(item.seller.id)
                else:
                    seller = str(item.seller)
        except Exception:
            pass

        return {
            "mercari_id": mercari_id,
            "title": str(item.name) if hasattr(item, "name") else "",
            "price": price,
            "image_url": image_url,
            "product_url": product_url,
            "condition": condition,
            "seller": seller,
        }
    except Exception as e:
        logger.warning(f"解析商品数据失败: {e}")
        return None


async def _maybe_await(result: Any) -> Any:
    """兼容同步/异步返回值"""
    if inspect.isawaitable(result):
        return await result
    return result


def _extract_items(results: Any) -> list:
    """兼容不同版本 mercapi 的返回结构"""
    if results is None:
        return []
    if isinstance(results, list):
        return results
    if hasattr(results, "items"):
        return list(getattr(results, "items") or [])
    if isinstance(results, dict) and "items" in results:
        return list(results.get("items") or [])
    return []


async def _search_with_category_fallback(
    mercari_client: Any, keyword_name: str, category_id: Optional[int]
) -> Any:
    """尝试不同的分类参数名以兼容 mercapi 版本差异"""
    try:
        from mercapi.requests.search import SearchRequestData
        status_filter = [SearchRequestData.Status.STATUS_ON_SALE]
    except ImportError:
        status_filter = []

    if not category_id:
        if status_filter:
            return await _maybe_await(mercari_client.search(keyword_name, status=status_filter))
        return await _maybe_await(mercari_client.search(keyword_name))

    attempts: Iterable[tuple[str, Any]] = (
        ("categories", [category_id]),
        ("category_id", category_id),
        ("category_ids", [category_id]),
    )
    for param_name, value in attempts:
        try:
            kwargs = {param_name: value}
            if status_filter:
                kwargs["status"] = status_filter
            return await _maybe_await(mercari_client.search(keyword_name, **kwargs))
        except TypeError as e:
            logger.warning(f"分类参数 {param_name} 不被支持，尝试其他参数: {e}")

    logger.warning("分类参数均不被支持，改为无分类搜索")
    if status_filter:
        return await _maybe_await(mercari_client.search(keyword_name, status=status_filter))
    return await _maybe_await(mercari_client.search(keyword_name))


async def crawl_keyword(db: Session, keyword_id: int, keyword_name: str, alert_price: float, category_id: Optional[int] = None):
    """爬取单个关键词的商品"""
    try:
        from mercapi import Mercapi
        m = Mercapi()

        cat_info = f" [分类:{category_id}]" if category_id else ""
        logger.info(f"开始爬取关键词: {keyword_name}{cat_info}")

        # 滚动覆盖：先删除该关键词的旧数据
        crud.delete_items_by_keyword(db, keyword_id)

        results = await _search_with_category_fallback(m, keyword_name, category_id)
        items = _extract_items(results)

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
                            "seller": item_data.get("seller", "未知卖家"),
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
