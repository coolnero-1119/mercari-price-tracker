import logging
import asyncio
from typing import Dict, Any
from app.config import settings

logger = logging.getLogger(__name__)

async def send_telegram_alert(keyword_name: str, alert_price: float, items: list) -> bool:
    """
    发送价格预警至 Telegram，通过子进程调用 openclaw 命令行工具，不阻塞主事件循环。
    """
    # 按照配置获取默认用户ID
    target = getattr(settings, "TELEGRAM_USER_ID", "7498035970")

    success_all = True
    for item in items:
        price = item.get("price", "N/A")
        title = item.get("title", "未知商品")
        product_url = item.get("product_url", "#")
        seller = item.get("seller", "未知卖家")

        # 构建 Telegram Markdown 格式消息
        msg_text = (
            f"🚨 **价格预警通知** 🚨\n\n"
            f"关键词 **{keyword_name}** 发现目标商品！\n"
            f"预警价格: `¥{alert_price:.0f}`\n"
            f"当前价格: `¥{price}`\n\n"
            f"商品标题: {title}\n"
            f"卖家信息: {seller}\n\n"
            f"[立即查看商品]({product_url})"
        )

        try:
            # 使用 asyncio create_subprocess_exec 调用命令行工具
            process = await asyncio.create_subprocess_exec(
                "openclaw", "message", "send",
                "--channel", "telegram",
                "--target", target,
                "--message", msg_text,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                logger.info(f"✅ Telegram 预警发送成功: {keyword_name}")
            else:
                logger.error(f"❌ Telegram 发送失败. Return code: {process.returncode}")
                if stderr:
                    logger.error(f"Stderr: {stderr.decode().strip()}")
                success_all = False

        except Exception as e:
            logger.error(f"❌ 调用 OpenClaw CLI 失败: {e}")
            success_all = False
            
    return success_all
