from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # 数据库
    DATABASE_URL: str = "sqlite:///./mercari_tracker.db"

    # 邮件配置
    SMTP_SERVER: str = "smtp.gmail.com"
    SMTP_PORT: int = 465
    EMAIL_ACCOUNT: str = "chenshuai11191@gmail.com"
    EMAIL_PASSWORD: str = "yiln cgng tduf cytr"
    EMAIL_RECIPIENT: str = "691708292@qq.com"

    # 调度配置（分钟）
    NORMAL_MIN_INTERVAL: int = 20
    NORMAL_MAX_INTERVAL: int = 40
    NIGHT_MIN_INTERVAL: int = 45
    NIGHT_MAX_INTERVAL: int = 90
    NIGHT_START_HOUR: int = 0
    NIGHT_END_HOUR: int = 7

    # 每个关键词最大获取商品数
    MAX_ITEMS_PER_KEYWORD: int = 100

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
