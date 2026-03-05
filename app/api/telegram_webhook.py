"""
Telegram Webhook 接收器

处理来自 Telegram Bot 的 callback_query（内联按钮回调）。
当用户点击「屏蔽此商品」按钮时，本接口接收请求并将该 mercari_id 写入数据库屏蔽列表。

注意：需要将 Telegram Bot Webhook 地址设置为:
  https://<your-domain>:8000/webhook/telegram
"""
import logging
import aiohttp
from fastapi import APIRouter, BackgroundTasks, Request
from app.database import SessionLocal
from app import crud
from app.email_service import BOT_TOKEN

logger = logging.getLogger(__name__)
router = APIRouter()


async def _answer_callback(callback_query_id: str, text: str):
    """回调 Telegram answerCallbackQuery，消除按钮的 loading 状态"""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/answerCallbackQuery"
    async with aiohttp.ClientSession() as session:
        await session.post(url, json={"callback_query_id": callback_query_id, "text": text, "show_alert": True})


async def _send_tg_message(chat_id: str, text: str):
    """向指定群组/用户发送确认消息"""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    async with aiohttp.ClientSession() as session:
        await session.post(url, json={"chat_id": chat_id, "text": text, "parse_mode": "HTML"})


async def _handle_block_callback(callback_query_id: str, chat_id: str, data: str):
    """解析 block:<mercari_id>:<title> 格式并写入数据库"""
    try:
        parts = data.split(":", 2)  # "block", mercari_id, title
        if len(parts) < 2:
            return
        mercari_id = parts[1]
        title = parts[2] if len(parts) > 2 else mercari_id

        db = SessionLocal()
        try:
            crud.block_item(db, mercari_id=mercari_id, title=title)
            logger.info(f"✅ 商品已屏蔽: {mercari_id} - {title}")
        finally:
            db.close()

        await _answer_callback(
            callback_query_id,
            f"🚫 已屏蔽「{title}」\n该商品不会再次出现！"
        )
        await _send_tg_message(
            chat_id,
            f"🚫 <b>商品已屏蔽</b>\n<code>{title}</code>\nMercari ID: <code>{mercari_id}</code>"
        )
    except Exception as e:
        logger.error(f"❌ 处理屏蔽回调失败: {e}")
        await _answer_callback(callback_query_id, "❌ 屏蔽失败，请稍后重试")


@router.post("/webhook/telegram", tags=["webhook"])
async def telegram_webhook(request: Request, background_tasks: BackgroundTasks):
    """
    接收来自 Telegram 的 Update 事件。
    目前只处理 callback_query（内联按钮点击）。
    """
    try:
        body = await request.json()
    except Exception:
        return {"ok": True}

    # 处理内联按钮回调
    callback_query = body.get("callback_query")
    if callback_query:
        callback_query_id = callback_query.get("id", "")
        data = callback_query.get("data", "")
        chat_id = str(callback_query.get("message", {}).get("chat", {}).get("id", ""))

        if data.startswith("block:"):
            background_tasks.add_task(
                _handle_block_callback, callback_query_id, chat_id, data
            )

    return {"ok": True}
