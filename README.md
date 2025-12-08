# Crystal 水晶 - 舆情哨塔

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10+-blue?logo=python" alt="Python">
  <img src="https://img.shields.io/badge/FastAPI-0.104+-green?logo=fastapi" alt="FastAPI">
  <img src="https://img.shields.io/badge/React-18-blue?logo=react" alt="React">
  <img src="https://img.shields.io/badge/Ant%20Design-5-blue?logo=antdesign" alt="Ant Design">
</p>

Crystal 是一个服务于量化交易系统的轻量级舆情监测微服务，每日从社交平台（微博、知乎、雪球）抓取舆情数据并进行可视化展示。

## ✨ 功能特性

- 📊 **多平台抓取** - 支持微博、知乎、雪球三大平台
- 🔐 **账号管理** - 平台账号状态管理与模拟登录
- 📋 **关注列表** - 灵活的 watchlist 管理（账号/股票/关键词）
- ⏰ **定时任务** - 每日 06:00 自动采集前一天舆情
- 🌙 **暗黑界面** - 极客风格的 Web 时间轴展示
- 🔌 **API 接口** - 对外提供 snapshot API

## 🚀 快速开始

### 1. 安装依赖

```bash
# 安装 Python 依赖
pip install -r requirements.txt

# 安装 Playwright 浏览器
playwright install chromium
```

### 2. 启动后端

```bash
# 开发模式
python -m uvicorn app.main:app --reload --port 8000
```

### 3. 启动前端

```bash
cd app/web
npm install
npm run dev
```

访问 http://localhost:5173 查看界面。

## 📁 项目结构

```
crystal/
├── app/
│   ├── main.py           # FastAPI 入口
│   ├── config/           # 配置管理
│   ├── core/             # 核心模型和 Schema
│   ├── storage/          # 数据库和存储
│   ├── account/          # 账号管理
│   ├── crawler/          # 爬虫模块
│   ├── scheduler/        # 定时任务
│   ├── api/              # API 路由
│   └── web/              # React 前端
├── scripts/              # 工具脚本
├── data/                 # SQLite 数据库
└── logs/                 # 日志文件
```

## 📡 API 接口

| 端点 | 方法 | 描述 |
|------|------|------|
| `/api/v1/health` | GET | 健康检查 |
| `/api/v1/auth/status` | GET | 账号状态 |
| `/api/v1/auth/login` | POST | 模拟登录 |
| `/api/v1/snapshot` | GET | 查询舆情数据 |
| `/api/v1/jobs` | GET | 查看定时任务 |
| `/api/v1/jobs/trigger` | POST | 手动触发任务 |

### 舆情快照接口

```
GET /api/v1/snapshot?symbol=600036.SH&from=2025-12-01&to=2025-12-08&keyword=订单
```

## ⚙️ 配置

通过环境变量或 `.env` 文件配置：

| 变量 | 默认值 | 描述 |
|------|--------|------|
| `DEBUG` | `false` | 调试模式 |
| `PORT` | `8000` | 服务端口 |
| `DAILY_JOB_HOUR` | `6` | 定时任务小时 |
| `HEADLESS` | `true` | Playwright 无头模式 |

## 📄 License

MIT