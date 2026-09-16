# API 文档

> Base URL: `http://localhost:8000/api/v1`
>
> 交互式文档(Swagger UI): http://localhost:8000/docs
>
> 所有 `POST`/`PUT`/`DELETE` 请求体为 JSON,需带 `Content-Type: application/json`。
> 文件上传端点除外(见 §5)。

---

## 测试前准备

1. 启动后端:`uvicorn app.main:app --reload --port 8000`
2. 在 `.env` 中填入 `DEEPSEEK_API_KEY`(聊天端点需要)
3. 建议测试顺序:商户 → 商品 → 会话 → 聊天 → 订单 → 知识库
4. 下文用 `{id}` 占位符表示上一步返回的 id

---

## 1. 商户 Merchant

### 1.1 创建商户

`POST /merchants`

```json
// Request Body
{
  "name": "数码旗舰店",
  "description": "主营智能音箱和耳机"
}
```

```json
// 201 Created
{
  "id": "a1b2c3...",
  "name": "数码旗舰店",
  "description": "主营智能音箱和耳机",
  "created_at": "2026-09-11T10:00:00Z"
}
```

**curl**:
```bash
curl -X POST http://localhost:8000/api/v1/merchants \
  -H "Content-Type: application/json" \
  -d '{"name":"数码旗舰店","description":"主营智能音箱和耳机"}'
```

### 1.2 商户列表

`GET /merchants`

```json
// 200
[
  { "id": "a1b2c3...", "name": "数码旗舰店", "description": "...", "created_at": "..." }
]
```

**curl**:
```bash
curl http://localhost:8000/api/v1/merchants
```

### 1.3 商户详情

`GET /merchants/{merchant_id}`

**curl**:
```bash
curl http://localhost:8000/api/v1/merchants/a1b2c3...
```

### 1.4 某商户的商品列表

`GET /merchants/{merchant_id}/products`

**curl**:
```bash
curl http://localhost:8000/api/v1/merchants/a1b2c3.../products
```

---

## 2. 商品 Product

### 2.1 上架商品(自动入向量库)

`POST /merchants/{merchant_id}/products`

```json
// Request Body
{
  "name": "智能云音箱 Pro",
  "description": "4英寸全频单元,30W,支持语音助手,适合卧室听音乐",
  "detail_content": "核心功能:语音助手控制、立体声播放。使用说明:长按顶部唤醒语音助手。售后政策:7天无理由退换,1年质保。",
  "price": "499.00",
  "specs": "尺寸:180x90x90mm;重量:1.2kg;蓝牙5.0;WiFi双频",
  "stock": 50,
  "image_url": ""
}
```

```json
// 201 Created
{
  "id": "p1q2r3...",
  "merchant_id": "a1b2c3...",
  "name": "智能云音箱 Pro",
  "description": "4英寸全频单元...",
  "detail_content": "核心功能:语音助手控制...",
  "price": "499.00",
  "specs": "尺寸:180x90x90mm;...",
  "stock": 50,
  "image_url": "",
  "status": "indexed",
  "created_at": "2026-09-11T10:05:00Z"
}
```

> `detail_content` 字段:商品的功能介绍、使用说明和售后政策,构成商品知识库,AI 客服据此回答用户问题。
>
> `status` 字段:`indexed`(已入向量库) / `failed`(索引失败但 DB 记录已保存)

**curl**:
```bash
curl -X POST http://localhost:8000/api/v1/merchants/a1b2c3.../products \
  -H "Content-Type: application/json" \
  -d '{"name":"智能云音箱 Pro","description":"4英寸全频单元,30W,适合卧室","price":"499.00","specs":"蓝牙5.0;WiFi双频","stock":50,"image_url":""}'
```

### 2.2 所有商品列表(消费者浏览)

`GET /products`

```json
// 200
[
  { "id": "p1q2r3...", "merchant_id": "a1b2c3...", "name": "智能云音箱 Pro", "price": "499.00", "status": "indexed", "..." : "..." }
]
```

**curl**:
```bash
curl http://localhost:8000/api/v1/products
```

### 2.3 商品详情

`GET /products/{product_id}`

**curl**:
```bash
curl http://localhost:8000/api/v1/products/p1q2r3...
```

### 2.4 更新商品(同步重建向量)

`PUT /products/{product_id}`

```json
// Request Body(所有字段可选,只传需要改的)
{
  "name": "智能云音箱 Pro(2025升级版)",
  "price": "459.00",
  "stock": 80,
  "detail_content": "新增功能:... 售后政策:..."
}
```

> 修改后自动重建向量索引,无需下架重建。

**curl**:
```bash
curl -X PUT http://localhost:8000/api/v1/products/p1q2r3... \
  -H "Content-Type: application/json" \
  -d '{"price":"459.00","stock":80}'
```

### 2.5 下架商品(同步删向量)

`DELETE /products/{product_id}`

```json
// 200
{ "ok": true }
```

**curl**:
```bash
curl -X DELETE http://localhost:8000/api/v1/products/p1q2r3...
```

---

## 3. 会话 Session

### 3.1 创建会话

`POST /sessions`

```json
// Request Body(title 可选,不传则默认"新会话")
{
  "title": "音箱咨询"
}
```

```json
// 201
{
  "id": "s1t2u3...",
  "title": "音箱咨询",
  "summary": null,
  "created_at": "...",
  "updated_at": "..."
}
```

**curl**:
```bash
curl -X POST http://localhost:8000/api/v1/sessions \
  -H "Content-Type: application/json" \
  -d '{"title":"音箱咨询"}'
```

### 3.2 会话列表

`GET /sessions?page=1&size=20`

```json
// 200
{
  "items": [ { "id": "s1t2u3...", "title": "音箱咨询", "..." : "..." } ],
  "total": 1
}
```

**curl**:
```bash
curl "http://localhost:8000/api/v1/sessions?page=1&size=20"
```

### 3.3 会话详情(含消息历史)

`GET /sessions/{session_id}`

```json
// 200
{
  "session": { "id": "s1t2u3...", "title": "音箱咨询", "..." : "..." },
  "messages": [
    {
      "id": 1,
      "session_id": "s1t2u3...",
      "role": "user",
      "content": "想买个卧室音箱",
      "sources_json": [],
      "product_cards_json": [],
      "created_at": "..."
    },
    {
      "id": 2,
      "session_id": "s1t2u3...",
      "role": "assistant",
      "content": "为您推荐智能云音箱 Pro...",
      "sources_json": [{"kind":"product","title":"智能云音箱 Pro","price":"499.00"}],
      "product_cards_json": [{"id":"p1q2r3...","name":"智能云音箱 Pro","price":"499.00"}],
      "created_at": "..."
    }
  ]
}
```

**curl**:
```bash
curl http://localhost:8000/api/v1/sessions/s1t2u3...
```

### 3.4 删除会话

`DELETE /sessions/{session_id}`

```json
// 200
{ "ok": true }
```

**curl**:
```bash
curl -X DELETE http://localhost:8000/api/v1/sessions/s1t2u3...
```

---

## 4. 聊天 Chat(SSE 流式)

### 4.1 发送消息

`POST /chat`

```json
// Request Body
{
  "session_id": "s1t2u3...",
  "message": "想买个卧室音箱,预算500以内"
}
```

**响应**: `text/event-stream`(SSE),逐行推送以下事件:

| 事件 type | 说明 | payload |
|---|---|---|
| `token` | 流式回答的文本片段 | `{"type":"token","content":"为您"}` |
| `tool_call` | LLM 调用了工具 | `{"type":"tool_call","name":"search_products_by_keyword","args":{"keyword":"..."}}` |
| `sources` | 引用来源 | `{"type":"sources","sources":[{"kind":"product","product_id":"...","title":"...","price":"..."}]}` |
| `product_cards` | 商品卡片 | `{"type":"product_cards","product_cards":[{"id":"...","name":"...","price":"...","image_url":"","description":"...","specs":"..."}]}` |
| `done` | 回答完成 | `{"type":"done","message_id":42}` |
| `error` | 出错 | `{"type":"error","message":"..."}` |
| `ping` | 保活心跳 | `{"type":"ping"}` |

**curl 测试 SSE**:
```bash
curl -N -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"session_id":"s1t2u3...","message":"想买个卧室音箱,预算500以内"}'
```

> `-N` 禁用缓冲,实时看到流式输出。
>
> 典型流程:
> - 需求模糊时 → LLM 先反问(只有 token 事件,无 tool_call)
> - 需求明确时 → tool_call 事件 → token 事件(基于商品信息的回答) → product_cards 事件 → done

**PowerShell 测试**:
```powershell
$body = @{ session_id = "s1t2u3..."; message = "想买个卧室音箱" } | ConvertTo-Json
Invoke-RestMethod -Uri "http://localhost:8000/api/v1/chat" -Method Post -Body $body -ContentType "application/json"
```
> PowerShell 不支持 SSE 流式消费,只能拿到完整响应。推荐用 curl 或浏览器。

---

## 5. 知识库 Knowledge Base

### 5.1 上传文档(自动解析+分块+入向量库)

`POST /kb/upload`

> `multipart/form-data`,字段名 `file`
>
> 支持格式: `.pdf` `.docx` `.xlsx` `.json` `.md` `.txt`

```json
// 201
{
  "doc_id": "d1e2f3...",
  "filename": "product_manual.pdf",
  "chunks": 12
}
```

**curl**:
```bash
curl -X POST http://localhost:8000/api/v1/kb/upload \
  -F "file=@backend/samples/product.md"
```

**PowerShell**:
```powershell
curl.exe -X POST http://localhost:8000/api/v1/kb/upload -F "file=@backend/samples/product.md"
```
> PowerShell 的 `curl` 是 `Invoke-WebRequest` 的别名,不支持 `-F`,需用 `curl.exe`。

### 5.2 文档列表

`GET /kb/documents`

```json
// 200
[
  { "id": "d1e2f3...", "filename": "product_manual.pdf", "doc_type": "pdf", "chunk_count": 12, "status": "indexed", "created_at": "..." }
]
```

**curl**:
```bash
curl http://localhost:8000/api/v1/kb/documents
```

### 5.3 删除文档(同步删向量)

`DELETE /kb/documents/{doc_id}`

```json
// 200
{ "ok": true, "removed_chunks": 12 }
```

**curl**:
```bash
curl -X DELETE http://localhost:8000/api/v1/kb/documents/d1e2f3...
```

### 5.4 重建所有文档索引(重置向量库)

`POST /kb/rebuild`

```json
// 200
{ "reindexed": 3 }
```

**curl**:
```bash
curl -X POST http://localhost:8000/api/v1/kb/rebuild
```

---

## 6. 订单 Order

### 6.1 单品下单

`POST /orders`

```json
// Request Body
{
  "session_id": "s1t2u3...",  // 可选,关联会话
  "product_id": "p1q2r3...",
  "quantity": 1,
  "remark": "尽快发货"
}
```

```json
// 201
{
  "id": "o1v2w3...",
  "session_id": "s1t2u3...",
  "merchant_id": "a1b2c3...",
  "status": "pending",
  "total_amount": "499.00",
  "remark": "尽快发货",
  "created_at": "...",
  "items": [
    {
      "id": 1,
      "product_id": "p1q2r3...",
      "product_name": "智能云音箱 Pro",
      "price": "499.00",
      "quantity": 1,
      "image_url": ""
    }
  ]
}
```

**curl**:
```bash
curl -X POST http://localhost:8000/api/v1/orders \
  -H "Content-Type: application/json" \
  -d '{"session_id":"s1t2u3...","product_id":"p1q2r3...","quantity":1,"remark":"尽快发货"}'
```

### 6.2 批量结算(购物车,按商户自动拆单)

`POST /orders/checkout`

```json
// Request Body
{
  "session_id": "s1t2u3...",
  "items": [
    { "product_id": "p1q2r3...", "quantity": 1 },
    { "product_id": "p4q5r6...", "quantity": 2 }
  ],
  "remark": "合并发货"
}
```

```json
// 201(返回多个订单,每个商户一条)
[
  { "id": "o1v2w3...", "merchant_id": "a1b2c3...", "status": "pending", "total_amount": "499.00", "items": [...], "..." : "..." },
  { "id": "o7x8y9...", "merchant_id": "z9y8x7...", "status": "pending", "total_amount": "398.00", "items": [...], "..." : "..." }
]
```

**curl**:
```bash
curl -X POST http://localhost:8000/api/v1/orders/checkout \
  -H "Content-Type: application/json" \
  -d '{"items":[{"product_id":"p1q2r3...","quantity":1},{"product_id":"p4q5r6...","quantity":2}],"remark":"合并发货"}'
```

### 6.3 订单列表

`GET /orders?session_id={session_id}&page=1&size=20`

| 参数 | 必填 | 说明 |
|---|---|---|
| `session_id` | 否 | 按会话过滤 |
| `page` | 否 | 页码,默认 1 |
| `size` | 否 | 每页条数,默认 20,最大 100 |

```json
// 200
{
  "items": [ { "id": "o1v2w3...", "status": "pending", "..." : "..." } ],
  "total": 1
}
```

**curl**:
```bash
curl "http://localhost:8000/api/v1/orders?session_id=s1t2u3...&page=1&size=20"
```

### 6.4 订单详情

`GET /orders/{order_id}`

**curl**:
```bash
curl http://localhost:8000/api/v1/orders/o1v2w3...
```

### 6.5 支付订单(模拟)

`POST /orders/{order_id}/pay`

```json
// 200
{ "id": "o1v2w3...", "status": "paid", "..." : "..." }
```

**错误场景**:
- 订单已支付 → `400 {"detail":"订单已支付,请勿重复支付"}`
- 订单已取消 → `400 {"detail":"订单已取消,无法支付"}`

**curl**:
```bash
curl -X POST http://localhost:8000/api/v1/orders/o1v2w3.../pay
```

### 6.6 取消订单

`POST /orders/{order_id}/cancel`

**错误场景**:
- 订单已支付 → `400 {"detail":"订单已支付,无法取消"}`
- 订单已取消 → `400 {"detail":"订单已取消"}`

**curl**:
```bash
curl -X POST http://localhost:8000/api/v1/orders/o1v2w3.../cancel
```

---

## 7. 健康检查 Health

`GET /health`

```json
// 200
{ "status": "ok" }
```

**curl**:
```bash
curl http://localhost:8000/api/v1/health
```

---

## 状态码速查

| 码 | 含义 | 触发场景 |
|---|---|---|
| 200 | 成功 | GET / PUT / DELETE / pay / cancel |
| 201 | 创建成功 | POST(merchants / products / sessions / orders) |
| 400 | 参数错误 | 空消息体、空购物车、重复支付/取消 |
| 404 | 不存在 | 商户/商品/会话/订单 ID 不存在 |
| 500 | 服务端错误 | LLM 调用失败、向量库索引失败 |

---

## 端到端测试流程(curl 版)

```bash
# 1. 创建商户
MERCHANT=$(curl -s -X POST http://localhost:8000/api/v1/merchants \
  -H "Content-Type: application/json" \
  -d '{"name":"数码旗舰店"}' | python -c "import sys,json; print(json.load(sys.stdin)['id'])")
echo "商户ID: $MERCHANT"

# 2. 上架商品
PRODUCT=$(curl -s -X POST http://localhost:8000/api/v1/merchants/$MERCHANT/products \
  -H "Content-Type: application/json" \
  -d '{"name":"智能云音箱 Pro","description":"4英寸全频单元 30W 适合卧室","price":"499.00","specs":"蓝牙5.0","stock":50}' \
  | python -c "import sys,json; print(json.load(sys.stdin)['id'])")
echo "商品ID: $PRODUCT"

# 3. 创建会话
SESSION=$(curl -s -X POST http://localhost:8000/api/v1/sessions \
  -H "Content-Type: application/json" \
  -d '{"title":"音箱咨询"}' | python -c "import sys,json; print(json.load(sys.stdin)['id'])")
echo "会话ID: $SESSION"

# 4. 聊天(SSE 流式,实时输出)
curl -N -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d "{\"session_id\":\"$SESSION\",\"message\":\"想买个卧室音箱,预算500以内\"}"

# 5. 单品下单
ORDER=$(curl -s -X POST http://localhost:8000/api/v1/orders \
  -H "Content-Type: application/json" \
  -d "{\"session_id\":\"$SESSION\",\"product_id\":\"$PRODUCT\",\"quantity\":1}" \
  | python -c "import sys,json; print(json.load(sys.stdin)['id'])")
echo "订单ID: $ORDER"

# 6. 支付订单
curl -X POST http://localhost:8000/api/v1/orders/$ORDER/pay

# 7. 查看订单列表
curl "http://localhost:8000/api/v1/orders?session_id=$SESSION"
```
