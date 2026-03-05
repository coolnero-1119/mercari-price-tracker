import asyncio
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import create_tables
from app.scheduler import start_scheduler, stop_scheduler
from app.api import keywords, products, stats, telegram_webhook
from app.telegram_poller import telegram_poll_loop

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时
    create_tables()
    logger.info("数据库表已初始化")
    start_scheduler()
    # 启动 Telegram 长轮询受理屏蔽按钮回调
    poll_task = asyncio.create_task(telegram_poll_loop())
    yield
    # 关闭时
    poll_task.cancel()
    stop_scheduler()


app = FastAPI(
    title="Mercari 价格追踪系统",
    description="自动追踪煤炉商品价格并发送预警邮件",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(keywords.router)
app.include_router(products.router)
app.include_router(stats.router)
app.include_router(telegram_webhook.router)


@app.get("/", tags=["root"])
def root():
    return {
        "service": "Mercari 价格追踪系统",
        "docs": "/docs",
        "status": "running",
    }
