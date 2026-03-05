import ssl
import aiohttp
import logging
import aiosmtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from app.config import settings

logger = logging.getLogger(__name__)

# Telegram Bot 设置（与 webhook handler 共享）
BOT_TOKEN = "8582502140:AAH_QAWlcKHbVA51En0QrZZm71N5CJgZQgU"
CHAT_ID = "-1003860744776"  # 推送目标群组 ID

def _build_markdown(keyword_name: str, alert_price: float, items: list[dict]) -> str:
    md_items = []
    
    for item in items:
        price = item.get("price", "N/A")
        title = item.get("title", "未知商品")
        product_url = item.get("product_url", "#")
        seller = item.get("seller", "未知卖家")
        md_items.append(f"📦 **{title}**\n💰 当前价格：¥{price} (卖家: {seller})\n🔗 [立刻查看商品]({product_url})\n---")

    items_text = "\n".join(md_items)

    return f"""🚨 **价格预警通知: {keyword_name}**

关键词 **{keyword_name}** 下有 **{len(items)}** 件商品价格达到预警线！
🔸 **预警价格：** ¥{alert_price:.0f}

**达标商品列表:**
{items_text}"""


def _build_html(keyword_name: str, alert_price: float, items: list[dict]) -> str:
    html_items = ""
    for item in items:
        price = item.get("price", "N/A")
        title = item.get("title", "未知商品")
        image_url = item.get("image_url", "")
        product_url = item.get("product_url", "#")
        seller = item.get("seller", "未知卖家")

        image_tag = f'<img src="{image_url}" alt="商品图片" style="max-width:300px;border-radius:8px;"/>' if image_url else ""
        
        html_items += f"""
        <div style="margin-top: 16px; border-bottom: 1px solid #eee; padding-bottom: 16px;">
            <p style="margin:4px 0 0;">当前价格：<strong style="color:#e74c3c;font-size:20px;">¥{price}</strong></p>
            {image_tag}
            <p style="font-size:15px;margin-top:16px;">{title}</p>
            <p style="font-size:14px;color:#666;margin-top:8px;">卖家信息：{seller}</p>
            <a href="{product_url}" style="display:inline-block;margin-top:16px;padding:12px 24px;background:#e74c3c;color:#fff;border-radius:6px;text-decoration:none;font-weight:bold;">
              立即查看商品 →
            </a>
        </div>
        """

    return f"""
<!DOCTYPE html>
<html lang="zh">
<head><meta charset="UTF-8"/></head>
<body style="font-family:Arial,sans-serif;background:#f5f5f5;padding:20px;">
  <div style="max-width:600px;margin:0 auto;background:#fff;border-radius:12px;overflow:hidden;box-shadow:0 2px 8px rgba(0,0,0,.1);">
    <div style="background:#e74c3c;color:#fff;padding:20px 24px;">
      <h1 style="margin:0;font-size:22px;">🚨 价格预警通知</h1>
    </div>
    <div style="padding:24px;">
      <p style="font-size:16px;">关键词 <strong>{keyword_name}</strong> 下有 <strong>{len(items)}</strong> 件商品价格达到预警线！</p>
      <div style="background:#fef9c3;border-left:4px solid #f59e0b;padding:12px 16px;border-radius:4px;margin-bottom:16px;">
        <p style="margin:0;">预警价格：<strong>¥{alert_price:.0f}</strong></p>
      </div>
      {html_items}
    </div>
    <div style="background:#f9f9f9;padding:12px 24px;font-size:12px;color:#999;">
      此邮件由 Mercari 价格追踪系统自动发送
    </div>
  </div>
</body>
</html>
"""


async def send_alert_email(keyword_name: str, alert_price: float, items: list[dict]) -> bool:
    """
    发送价格预警至 OpenClaw (Telegram) 以及 Email 邮箱，返回是否至少有一种推送成功
    """
    if not items:
        return True
        
    webhook_success = False
    email_success = False

    # 1. Telegram 机器人直接推送 (精美图文卡片)
    bot_token = BOT_TOKEN
    chat_id = CHAT_ID

    try:
        async with aiohttp.ClientSession() as session:
            # 1.1 发送顶部摘要说明
            summary_text = f"🚨 <b>价格预警: {keyword_name}</b>\n发现 <b>{len(items)}</b> 件降价商品！\n🔸 预警线: ¥{alert_price:.0f}"
            await session.post(
                f"https://api.telegram.org/bot{bot_token}/sendMessage",
                json={"chat_id": chat_id, "text": summary_text, "parse_mode": "HTML"}
            )
            
            # 1.2 循环发送每一个带有 InlineKeyboard (内置按钮) 的精美相册卡片
            for item in items:
                price = item.get("price", "N/A")
                title = item.get("title", "未知商品").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                seller = item.get("seller", "未知卖家").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                product_url = item.get("product_url", "#")
                image_url = item.get("image_url") or "https://www.mercari.com/favicon.ico"
                
                mercari_id = item.get("mercari_id", "")
                short_title = item.get("title", "")[:30]
                block_callback = f"block:{mercari_id}:{short_title}"

                payload = {
                    "chat_id": chat_id,
                    "photo": image_url,
                    "caption": f"📦 <b>{title}</b>\n💰 当前价格：¥{price} (卖家: {seller})",
                    "parse_mode": "HTML",
                    "reply_markup": {
                        "inline_keyboard": [
                            [{"text": "🔗 立刻查看商品", "url": product_url}],
                            [{"text": "🚫 屏蔽此商品", "callback_data": block_callback}]
                        ]
                    }
                }
                resp = await session.post(f"https://api.telegram.org/bot{bot_token}/sendPhoto", json=payload)
                
                if resp.status != 200:
                    # 如果由于某种原因(图片失效/无法拉取)导致发图失败，降级发送纯文字附带链接预览
                    fallback_text = f"📦 <b>{title}</b>\n💰 ¥{price} (卖家: {seller})\n<a href='{product_url}'>🔗 立刻查看商品</a>"
                    await session.post(
                        f"https://api.telegram.org/bot{bot_token}/sendMessage",
                        json={"chat_id": chat_id, "text": fallback_text, "parse_mode": "HTML", "disable_web_page_preview": False}
                    )
                    
            logger.info(f"✅ Telegram API 图文队列预警直推成功: {keyword_name} ({len(items)}件)")
            webhook_success = True
            
    except Exception as e:
        logger.error(f"❌ Telegram API 网络请求出错: {e}")

    # 2. 传统 SMTP 邮件推送 (保留逻辑，若 465 解封后自动生效)
    subject = f"🚨 批量价格预警: {keyword_name} ({len(items)}件)"
    html_content = _build_html(keyword_name, alert_price, items)

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = settings.EMAIL_ACCOUNT
    msg["To"] = settings.EMAIL_RECIPIENT
    msg.attach(MIMEText(html_content, "html", "utf-8"))

    try:
        ssl_context = ssl.create_default_context()
        await aiosmtplib.send(
            msg,
            hostname=settings.SMTP_SERVER,
            port=settings.SMTP_PORT,
            use_tls=True,
            tls_context=ssl_context,
            username=settings.EMAIL_ACCOUNT,
            password=settings.EMAIL_PASSWORD,
        )
        logger.info(f"✅ 邮件发送成功: {subject}")
        email_success = True
    except Exception as e:
        logger.error(f"❌ 邮件发送失败: {e}")

    # 只要有一个途径发送成功，就认为是成功的预警记录
    return webhook_success or email_success
