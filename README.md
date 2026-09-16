# 智选商城

基于 RAG 的电商智能导购系统。AI 客服通过向量检索商品知识库为用户推荐商品，用户点击卡片自助下单。

## 技术栈

| 层 | 技术 |
|---|---|
| 后端 | FastAPI + SQLAlchemy + SQLite |
| 向量库 | Chroma + 本地 BGE embedding |
| LLM | DeepSeek（工具调用） |
| 前端 | Vue 3 + TypeScript + Element Plus + Vite |
| 流式 | SSE（Server-Sent Events） |

## 核心特性

- **智能导购**：AI 根据用户需求检索商品，返回多个匹配结果，支持排除条件跨轮次记忆（如"不要华为"）
- **商品知识库**：每个商品的基本信息 + 功能介绍与使用说明 + 售后政策，一起索引到向量库，AI 基于此回答
- **商品管理**：商户可动态编辑商品（无需下架重建），修改后自动重新索引
- **双端入口**：消费者登录页 `/login`，商户登录页 `/merchant/login`
- **购物车**：localStorage 持久化，按商户自动拆单结算
- **订单**：支持单品购买和购物车批量结算，支付/取消有幂等校验

## 项目结构

```
myproject1/
├── backend/
│   ├── .env                  # 环境变量（API Key 等）
│   ├── app/
│   │   ├── main.py           # FastAPI 入口
│   │   ├── config.py         # 配置加载
│   │   ├── api/v1/            # 路由
│   │   │   ├── chat.py        # SSE 聊天端点
│   │   │   ├── products.py    # 商品 CRUD
│   │   │   ├── orders.py      # 订单
│   │   │   ├── merchants.py   # 商户
│   │   │   ├── sessions.py    # 会话
│   │   │   └── kb.py          # 知识库文档
│   │   ├── core/
│   │   │   ├── prompts.py     # 系统提示词
│   │   │   └── vector_store.py# Chroma 向量库
│   │   ├── rag/
│   │   │   ├── chain.py       # LLM + 工具调用链
│   │   │   ├── tools.py       # 检索工具
│   │   │   ├── memory.py      # 对话记忆 + 摘要
│   │   │   ├── session_store.py# 会话存储
│   │   │   └── product_indexer.py # 商品向量化
│   │   ├── schemas/           # Pydantic 模型
│   │   └── storage/
│   │       ├── models.py      # SQLAlchemy 模型
│   │       └── database.py    # DB 初始化 + 自动迁移
│   ├── seed.py                # 数据导入脚本
│   └── .venv/                 # Python 虚拟环境
├── frontend/
│   ├── vite.config.ts         # Vite 配置（代理 /api → 8000）
│   └── src/
│       ├── main.ts
│       ├── api/               # HTTP 客户端
│       ├── router/            # 路由 + 角色守卫
│       ├── stores/            # Pinia 状态管理
│       ├── styles/main.css   # 全局样式变量
│       ├── views/             # 页面
│       │   ├── LoginView.vue       # 消费者登录
│       │   ├── MerchantLoginView.vue # 商户登录
│       │   ├── ProductsView.vue    # 商城
│       │   ├── ChatView.vue        # 智能导购
│       │   ├── OrdersView.vue      # 我的订单
│       │   └── MerchantView.vue    # 商户后台
│       └── components/
│           ├── chat/          # 聊天组件
│           ├── shop/          # 商城组件
│           ├── merchant/      # 商户管理组件
│           └── layout/        # 布局组件
├── images/                    # 商品图片（按品类分目录）
├── goods_info.csv             # 商品数据源
├── start.ps1                  # 一键启动脚本
├── README.md
└── API.md                     # API 文档
```

## 快速启动

### 一键启动

```powershell
.\start.ps1
```

### 手动启动

**后端**（终端 1）：
```powershell
cd backend
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

**前端**（终端 2）：
```powershell
cd frontend
npx vite
```

### 环境配置

1. 后端 `.env` 文件中填入 `DEEPSEEK_API_KEY`（AI 对话必需）
2. 首次运行需初始化数据库：`python seed.py`
3. 前端依赖安装：`cd frontend; npm install`

### 访问地址

| 入口 | URL |
|---|---|
| 消费者登录 | http://localhost:5173/login |
| 商户登录 | http://localhost:5173/merchant/login |
| API 文档 | http://localhost:8000/docs |
| 健康检查 | http://localhost:8000/api/v1/health |

## 数据导入

从 CSV 导入真实商品数据：

```powershell
cd backend
.\.venv\Scripts\python.exe seed.py
```

这会清空旧数据并从 `goods_info.csv` 导入商品，同步索引到向量库。

## 角色说明

| 角色 | 入口 | 功能 |
|---|---|---|
| 消费者 | `/login` | 浏览商城、智能导购对话、购物车、下单、查看订单 |
| 商户 | `/merchant/login` | 上架/编辑/下架商品、填写功能介绍与售后政策（构成知识库） |
