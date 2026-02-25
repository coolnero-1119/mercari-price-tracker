# 煤炉价格追踪系统 - 完整需求文档

## 一、核心功能需求

| 功能模块 | 详细说明 |
|---------|---------|
| **关键词管理** | 添加、删除、修改关键词及其预警价格 |
| **爬虫调度** | 每20-40分钟随机间隔爬取，夜间(0-7点)降低频率到45-90分钟 |
| **邮件预警** | 当商品价格 ≤ 预警价格时，自动发送邮件通知 |
| **数据展示** | 提供Web API接口随时查看当前爬取的所有商品信息 |
| **滚动覆盖** | 每次新爬取自动覆盖上次的商品数据（保留价格历史） |

---

## 二、技术栈

```
- Python 3.12+
- mercapi (煤炉API库)
- FastAPI (Web API接口)
- SQLAlchemy + SQLite (数据存储)
- aiosmtplib (异步邮件发送)
- APScheduler (任务调度)
```

---

## 三、邮件配置

```
SMTP服务器: smtp.gmail.com
端口: 465 (SSL)
邮箱账号: chenshuai11191@gmail.com
应用专用密码: yiln cgng tduf cytr
收件人: 691708292@qq.com
```

---

## 四、数据库模型

### 4.1 keywords - 关键词表

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Integer PK | 主键 |
| name | String(200) | 关键词名称 |
| alert_price | Float | 预警价格 |
| is_active | Boolean | 是否启用 |
| created_at | DateTime | 创建时间 |
| updated_at | DateTime | 更新时间 |

### 4.2 items - 商品表（滚动覆盖）

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Integer PK | 主键 |
| mercari_id | String(50) | 煤炉商品ID |
| keyword_id | Integer FK | 关联关键词ID |
| title | String(500) | 商品标题 |
| price | Integer | 当前价格 |
| image_url | String | 图片链接 |
| product_url | String | 商品链接 |
| condition | String | 商品状态 |
| created_at | DateTime | 创建时间 |
| updated_at | DateTime | 更新时间 |

### 4.3 price_history - 价格历史表

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Integer PK | 主键 |
| item_id | Integer FK | 关联商品ID |
| price | Float | 价格 |
| recorded_at | DateTime | 记录时间 |

### 4.4 alert_logs - 预警记录表

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Integer PK | 主键 |
| keyword_id | Integer FK | 关联关键词ID |
| item_id | Integer FK | 关联商品ID |
| alert_price | Float | 预警价格 |
| actual_price | Float | 实际价格 |
| email_sent | Boolean | 邮件是否发送 |
| created_at | DateTime | 创建时间 |

---

## 五、API接口

### 5.1 关键词管理

```
GET    /api/keywords                # 获取所有关键词
POST   /api/keywords              # 添加关键词 {name, alert_price}
GET    /api/keywords/{id}          # 获取单个关键词
PUT    /api/keywords/{id}          # 修改关键词
DELETE /api/keywords/{id}          # 删除关键词
```

### 5.2 商品管理

```
GET /api/products                  # 获取所有商品（支持keyword_id筛选）
GET /api/products/{id}             # 获取单个商品
GET /api/products/by-keyword/{keyword_id}  # 按关键词获取商品
```

### 5.3 统计与历史

```
GET /api/price-history/{product_id}    # 获取价格历史
GET /api/stats                         # 获取统计信息
```

### 5.4 手动触发

```
POST /api/trigger-crawl                # 手动触发爬取
```

---

## 六、爬虫逻辑

```python
# 核心流程
1. 从数据库获取启用的关键词列表
2. 清空商品表（滚动覆盖）
3. 对每个关键词:
   - 搜索商品
   - 保存商品信息
   - 检查价格是否 ≤ 预警价格
   - 触发邮件通知
   - 记录预警日志
4. 随机间隔后下一次爬取
```

---

## 七、调度器配置

```python
# 正常时段 (7:00-24:00)
min_interval = 20  # 分钟
max_interval = 40  # 分钟

# 夜间时段 (0:00-7:00)
night_min_interval = 45  # 分钟
night_max_interval = 90  # 分钟
```

---

## 八、邮件通知模板

```html
主题: 🚨 价格预警: {keyword_name} - ¥{price}
内容: HTML格式，包含：
- 关键词名称
- 预警价格
- 商品图片
- 商品标题
- 当前价格
- 卖家信息
- 查看链接按钮
```

---

## 九、开发完成后

开发完成后告诉我：

1. **代码已推送到 GitHub** - 提供仓库地址
2. **如何安装依赖和启动** - 提供命令
3. **API 访问地址** - 默认 http://localhost:8000

我会立即测试所有功能并部署运行！🚀
