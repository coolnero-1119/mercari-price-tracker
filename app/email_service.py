import ssl
import logging
import aiosmtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from app.config import settings

logger = logging.getLogger(__name__)


def _build_html(keyword_name: str, alert_price: float, item: dict) -> str:
    price = item.get("price", "N/A")
    title = item.get("title", "未知商品")
    image_url = item.get("image_url", "")
    product_url = item.get("product_url", "#")

    image_tag = f'<img src="{image_url}" alt="商品图片" style="max-width:300px;border-radius:8px;"/>' if image_url else ""

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
      <p style="font-size:16px;">关键词 <strong>{keyword_name}</strong> 下有商品价格达到预警线！</p>
      <div style="background:#fef9c3;border-left:4px solid #f59e0b;padding:12px 16px;border-radius:4px;margin-bottom:16px;">
        <p style="margin:0;">预警价格：<strong>¥{alert_price:.0f}</strong></p>
        <p style="margin:4px 0 0;">当前价格：<strong style="color:#e74c3c;font-size:20px;">¥{price}</strong></p>
      </div>
      {image_tag}
      <p style="font-size:15px;margin-top:16px;">{title}</p>
      <a href="{product_url}" style="display:inline-block;margin-top:16px;padding:12px 24px;background:#e74c3c;color:#fff;border-radius:6px;text-decoration:none;font-weight:bold;">
        立即查看商品 →
      </a>
    </div>
    <div style="background:#f9f9f9;padding:12px 24px;font-size:12px;color:#999;">
      此邮件由 Mercari 价格追踪系统自动发送
    </div>
  </div>
</body>
</html>
"""


async def send_alert_email(keyword_name: str, alert_price: float, item: dict) -> bool:
    """
    发送价格预警邮件，返回是否成功
    """
    subject = f"🚨 价格预警: {keyword_name} - ¥{item.get('price', '?')}"
    html_content = _build_html(keyword_name, alert_price, item)

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = settings.EMAIL_ACCOUNT
    msg["To"] = settings.EMAIL_RECIPIENT
    msg.attach(MIMEText(html_content, "html", "utf-8"))

    try:
        # 调试环境免去SMTP，直接输出到本地方便查阅
        with open("test_email_output.html", "w", encoding="utf-8") as f:
            f.write(html_content)
        logger.info(f"邮件内容已保存到 test_email_output.html: {subject}")
        return True
    except Exception as e:
        logger.error(f"邮件保存失败: {e}")
        return False
