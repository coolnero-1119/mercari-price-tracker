"""
Telegram 长轮询后台任务

代替 Webhook 方案，使用长轮询（Long Polling）方式监听 Telegram Bot 的
callback_query 事件（内联按钮回调），无需 HTTPS 即可正常工作。

在 main.py 的 lifespan 中启动此任务。
"""
import asyncio
import logging
import aiohttp
from app.database import SessionLocal
from app import crud
from app.email_service import BOT_TOKEN, CHAT_ID

logger = logging.getLogger(__name__)

_POLL_URL = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates"
_ANSWER_URL = f"https://api.telegram.org/bot{BOT_TOKEN}/answerCallbackQuery"
_MSG_URL = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"


async def _answer_callback(session: aiohttp.ClientSession, callback_query_id: str, text: str):
    try:
        await session.post(_ANSWER_URL, json={
            "callback_query_id": callback_query_id,
            "text": text,
            "show_alert": True,
        })
    except Exception as e:
        logger.warning(f"answerCallbackQuery 失败: {e}")


async def _send_message(session: aiohttp.ClientSession, chat_id: str, text: str):
    try:
        await session.post(_MSG_URL, json={
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "HTML",
        })
    except Exception as e:
        logger.warning(f"sendMessage 失败: {e}")


async def _handle_block(session: aiohttp.ClientSession, callback_query: dict):
    callback_query_id = callback_query.get("id", "")
    data = callback_query.get("data", "")
    chat_id = str(callback_query.get("message", {}).get("chat", {}).get("id", CHAT_ID))

    if not data.startswith("block:"):
        return

    parts = data.split(":", 2)
    mercari_id = parts[1] if len(parts) > 1 else ""
    title = parts[2] if len(parts) > 2 else mercari_id

    if not mercari_id:
        return

    db = SessionLocal()
    try:
        crud.block_item(db, mercari_id=mercari_id, title=title)
        logger.info(f"✅ 商品已屏蔽 (来自 Telegram 按钮): {mercari_id} - {title}")
    finally:
        db.close()

    await _answer_callback(session, callback_query_id, f"🚫 已屏蔽「{title}」\n该商品不会再次出现！")
    await _send_message(session, chat_id, f"🚫 <b>商品已屏蔽</b>\n{title}\nID: <code>{mercari_id}</code>")


async def telegram_poll_loop():
    """
    永远运行的长轮询循环，监听并处理 callback_query 事件。
    使用 offset 保证消息只处理一次。
    """
    offset = 0
    logger.info("📡 Telegram 长轮询已启动，等待按钮回调...")
    
    async with aiohttp.ClientSession() as session:
        while True:
            try:
                params = {
                    "timeout": 30,
                    "allowed_updates": ["callback_query"],
                    "offset": offset,
                }
                async with session.get(_POLL_URL, params=params, timeout=aiohttp.ClientTimeout(total=40)) as resp:
                    if resp.status != 200:
                        await asyncio.sleep(5)
                        continue
                    data = await resp.json()
                    updates = data.get("result", [])
                    
                    for update in updates:
                        offset = update["update_id"] + 1
                        callback_query = update.get("callback_query")
                        if callback_query:
                            asyncio.create_task(_handle_block(session, callback_query))
                            
            except asyncio.CancelledError:
                logger.info("Telegram 长轮询已取消，退出")
                break
            except Exception as e:
                logger.warning(f"Telegram 长轮询出现异常，5 秒后重试: {e}")
                await asyncio.sleep(5)
