# Mercari 价格追踪系统

自动追踪煤炉（Mercari Japan）商品价格，价格达到预警线时自动发送邮件通知。支持按商品分类精准筛选，避免搜索结果混杂无关商品。

---

## 功能特性

- **关键词管理**：增删改查，支持随时启用/暂停
- **分类筛选**：通过 `category_id` 精准锁定商品类别（如只搜滑雪板，过滤掉车模）
- **自动爬取**：每 20-40 分钟随机间隔爬取；夜间 0-7 点降低至 45-90 分钟
- **预警通知**：商品价格 ≤ 预警价格时，自动发送 HTML 邮件，并直接推送到个人的 Telegram 获取通知
- **一键屏蔽**：在 Telegram 推送卡片上点击「🚫 屏蔽此商品」，该商品就不再推送
- **屏蔽管理**：通过 API 查看和解除屏蔽列表
- **仅看在售**：内置状态过滤，系统只抓取当前仍在售卖的有效商品，过滤历史废弃链接
- **数据管理**：每次爬取滚动覆盖商品数据，同时保留完整价格历史
- **Web API**：FastAPI 提供完整 REST 接口 + Swagger 可视化文档
- **后台守护**：完美支持 Systemd 接管，实现崩溃自动重启与开机自启动

---

## 安装 & 启动

```bash
# 1. 克隆项目
git clone https://github.com/coolnero-1119/mercari-price-tracker.git
cd mercari-price-tracker

# 2. 创建虚拟环境
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

# 3. 安装依赖
pip install -r requirements.txt

# 4. 启动服务
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

服务启动后会**立即执行第一次爬取**，之后按随机间隔自动爬取。

| 地址 | 说明 |
|------|------|
| http://localhost:8000 | 服务状态 |
| http://localhost:8000/docs | Swagger 可视化文档（推荐） |

---

## 生产部署 (Systemd 开机自启)

如需后台安全持久化运行，请建立 Systemd 进程服务：

```bash
# 1. 写入配置文件
sudo nano /etc/systemd/system/mercari-tracker.service
```

填入以下内容（注意替换为您自己的绝对路径）：
```ini
[Unit]
Description=Mercari Price Tracker FastAPI Service
After=network.target

[Service]
User=root
Group=root
WorkingDirectory=/root/mercari-price-tracker
Environment="PATH=/root/mercari-price-tracker/.venv/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
ExecStart=/root/mercari-price-tracker/.venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000
StandardOutput=append:/root/mercari-price-tracker/server.log
StandardError=append:/root/mercari-price-tracker/server.log
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

```bash
# 2. 启用并启动守护进程
sudo systemctl daemon-reload
sudo systemctl enable mercari-tracker.service
sudo systemctl restart mercari-tracker.service

# 查看实时运行日志
tail -f server.log
```

---

## 使用方法

### 1. 添加关键词 & 预警价格

**推荐：打开 http://localhost:8000/docs，使用 Swagger 界面操作**

或通过 curl：

```bash
# 添加关键词（指定分类，精准筛选）
curl -X POST http://localhost:8000/api/keywords \
  -H "Content-Type: application/json" \
  -d '{"name": "gray type r", "alert_price": 100000, "category_id": 887}'

# 添加关键词（不限分类）
curl -X POST http://localhost:8000/api/keywords \
  -H "Content-Type: application/json" \
  -d '{"name": "Nintendo Switch", "alert_price": 15000}'
```

请求字段说明：

| 字段 | 必填 | 说明 |
|------|------|------|
| `name` | ✅ | 搜索关键词，支持中英日文 |
| `alert_price` | ✅ | 预警价格（日元），商品价格 ≤ 此值时发邮件 |
| `category_id` | ❌ | 分类 ID（见下方常用分类表），不填则搜索全部分类 |
| `is_active` | ❌ | 是否启用，默认 `true` |

### 2. 常用商品分类 ID

| 分类 | ID |
|------|----|
| スノーボード（滑雪板） | `887` |
| スキー（滑雪橇） | `886` |
| ゴルフクラブ（高尔夫球杆） | `806` |
| 自転車（自行车） | `668` |
| ギター（吉他） | `224` |
| カメラ（相机） | `1` |
| ミニカー・車模型（车模） | `7380` |

> 不确定分类 ID 时，可先不填 `category_id` 搜一次，从返回商品的标题中确认目标类别，再通过 `PUT` 接口更新关键词加上 `category_id`。

### 3. 管理关键词

```bash
# 查看所有关键词
curl http://localhost:8000/api/keywords

# 修改预警价格
curl -X PUT http://localhost:8000/api/keywords/1 \
  -H "Content-Type: application/json" \
  -d '{"alert_price": 80000}'

# 暂停某关键词（停止爬取但保留数据）
curl -X PUT http://localhost:8000/api/keywords/1 \
  -H "Content-Type: application/json" \
  -d '{"is_active": false}'

# 删除关键词（同时删除关联商品）
curl -X DELETE http://localhost:8000/api/keywords/1
```

### 4. 查看商品 & 统计

```bash
# 查看所有商品
curl http://localhost:8000/api/products

# 查看指定关键词的商品（keyword_id 为添加时返回的 id）
curl "http://localhost:8000/api/products?keyword_id=1"

# 查看某商品的价格历史
curl http://localhost:8000/api/price-history/1

# 查看预警触发记录
curl http://localhost:8000/api/alert-logs

# 查看统计信息（关键词数、商品总数、预警次数、最后爬取时间）
curl http://localhost:8000/api/stats

# 手动立即触发一次爬取
curl -X POST http://localhost:8000/api/trigger-crawl
```

### 5. 管理屏蔽列表

屏蔽功能说明：屏蔽的商品即便价格再度低于预警线，也不会再次推送。

```bash
# 查看所有已屏蔽的商品
curl http://localhost:8000/api/blocked-items

# 解除屏蔽（用商品的 Mercari ID，从屏蔽列表中取得）
curl -X DELETE http://localhost:8000/api/blocked-items/m123456789
```

屏蔽操作 **不需要进入服务器**，在 Telegram 群组里点击商品卡片上的「🚫 屏蔽此商品」按钮即可完成。

> 提示：屏蔽列表也可在 Swagger 界面操作：http://localhost:8000/docs

---

## 调度规则

| 时段 | 爬取间隔 |
|------|---------|
| 7:00 - 24:00（正常） | 随机 20-40 分钟 |
| 0:00 - 7:00（夜间） | 随机 45-90 分钟 |

---

## 预警通知

当爬取到的商品价格 ≤ 设置的 `alert_price` 时，系统自动通过以发送通知：

### 1. Telegram 群组图文预警通知（主要途径）
系统内置对接了 Telegram Bot API，直接将高颜值的富文本图文卡片推送到个人或群组聊天框。需要在 `app/email_service.py` 代码内直接配置目标 Bot Token 与群组/联系人 ID (目前代码默认为测试群组)。

### 2. Email 邮件预警
系统支持标准的 SMTP (端口 465 SSL) 连接发送内容详尽的 HTML 安全邮件，内容包含：
- 关键词名称 & 预警价格
- 商品图片、标题、当前价格
- 卖家详细信息
- 一键跳转查看商品的专属按钮

> ⚠️ 注意：如部署在 DigitalOcean 等具有出站防火墙规则限制的云服务器上，可能需要提工单请求解除 `465` 端口封锁才能成功发送。目前通过内置的 Telegram 回调，即使无视该封禁限制依然可以秒推群组！

---

## 项目结构

```
mercari-price-tracker/
├── main.py                # FastAPI 入口 + 生命周期管理
├── requirements.txt       # 依赖列表
├── app/
│   ├── config.py          # 邮件、调度参数配置
│   ├── database.py        # SQLAlchemy 数据库连接
│   ├── models.py          # 数据库模型（4张表）
│   ├── schemas.py         # Pydantic 序列化模型
│   ├── crud.py            # 数据库 CRUD 操作
│   ├── crawler.py         # Mercari 爬虫（支持分类筛选）
│   ├── email_service.py   # Gmail 异步邮件发送
│   ├── scheduler.py       # 随机间隔调度循环
│   └── api/
│       ├── keywords.py    # 关键词 CRUD 接口
│       ├── products.py    # 商品查询接口
│       └── stats.py       # 统计、历史、手动触发接口
```

---

## 技术栈

| 组件 | 库 |
|------|----|
| Web 框架 | FastAPI |
| 数据库 | SQLite + SQLAlchemy |
| Mercari API | mercapi |
| 邮件发送 | aiosmtplib |
| 定时调度 | APScheduler |
