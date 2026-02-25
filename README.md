# Mercari 价格追踪系统

自动追踪煤炉（Mercari Japan）商品价格，价格达到预警线时发送邮件通知。

## 功能特性

- 关键词管理（增删改查）
- 每 20-40 分钟自动爬取（夜间 45-90 分钟）
- 价格 ≤ 预警价格时自动发邮件
- 商品数据滚动覆盖 + 价格历史保留
- FastAPI Web 接口

## 安装 & 启动

```bash
# 1. 进入项目目录
cd /Users/chenshuai/cs/mercari

# 2. 创建虚拟环境
python3 -m venv .venv
source .venv/bin/activate

# 3. 安装依赖
pip install -r requirements.txt

# 4. 启动服务
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

## API 访问

| 地址 | 说明 |
|------|------|
| http://localhost:8000 | 服务状态 |
| http://localhost:8000/docs | Swagger 交互文档 |
| http://localhost:8000/api/keywords | 关键词列表 |
| http://localhost:8000/api/products | 商品列表 |
| http://localhost:8000/api/stats | 统计信息 |

## 快速测试

```bash
# 添加关键词
curl -X POST http://localhost:8000/api/keywords \
  -H "Content-Type: application/json" \
  -d '{"name": "iPhone 15", "alert_price": 50000}'

# 手动触发爬取
curl -X POST http://localhost:8000/api/trigger-crawl

# 查看商品
curl http://localhost:8000/api/products
```

## 项目结构

```
mercari/
├── main.py                # FastAPI 入口
├── requirements.txt
├── app/
│   ├── config.py          # 配置（邮件/调度参数）
│   ├── database.py        # SQLAlchemy 数据库连接
│   ├── models.py          # 数据库模型
│   ├── schemas.py         # Pydantic 序列化模型
│   ├── crud.py            # 数据库操作
│   ├── crawler.py         # Mercari 爬虫
│   ├── email_service.py   # 邮件发送
│   ├── scheduler.py       # 定时调度
│   └── api/
│       ├── keywords.py    # 关键词 API
│       ├── products.py    # 商品 API
│       └── stats.py       # 统计 & 历史 API
```
