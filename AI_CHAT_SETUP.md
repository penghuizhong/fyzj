# 方圆智版 AI 聊天功能启动指南

## 当前状态

✅ **后端服务**: 已启动，端口8001  
✅ **基础设施**: PostgreSQL、Redis、Casdoor 运行正常  
✅ **JWT认证**: 已配置RS256公钥验证  
✅ **AI Agent**: rag-assistant 和 chatbot 已加载  

## 快速启动步骤

### 1. 启动基础设施（如果尚未启动）

```bash
cd /Users/mac/fyzj
docker compose up -d
```

这会启动：
- PostgreSQL (端口5432)
- Redis (端口6379)  
- Casdoor (端口8000)

### 2. 启动后端服务（已运行）

```bash
cd /Users/mac/fyzj/agent_api
docker compose up -d
```

服务运行在 http://localhost:8001

### 3. 启动前端开发服务器

```bash
cd /Users/mac/fyzj/web
pnpm install  # 如果尚未安装
pnpm dev
```

前端运行在 http://localhost:3000

## 认证流程

### 1. 访问前端页面
打开 http://localhost:3000

### 2. 登录
- 点击登录按钮，会跳转到 Casdoor 登录页面
- 默认管理员账号：`admin` / `123`
- 登录成功后会自动返回前端

### 3. 使用AI聊天
- 在底部输入框输入问题
- 按 Enter 或点击发送按钮
- 会看到打字机效果的流式响应

## API测试

### 测试健康检查（无需认证）
```bash
curl http://localhost:8001/health
```

### 测试AI聊天（需要JWT）

1. 先通过前端登录获取JWT token
2. 复制浏览器的 accessToken（从LocalStorage或Cookie中获取）
3. 测试流式接口：

```bash
curl -N -X POST http://localhost:8001/rag-assistant/stream \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN_HERE" \
  -d '{
    "message": "你好，请介绍一下自己",
    "stream_tokens": true
  }'
```

### 测试非流式接口
```bash
curl -X POST http://localhost:8001/rag-assistant/invoke \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN_HERE" \
  -d '{
    "message": "你好"
  }'
```

## 故障排查

### 1. JWT验证失败
- 确保已登录（前端显示用户信息）
- 检查浏览器Console是否有token相关错误
- 检查后端日志：`docker logs ai-server`

### 2. API连接失败
- 确认后端服务运行：`curl http://localhost:8001/health`
- 检查前端 `.env` 文件中的 `NEXT_PUBLIC_API_URL`

### 3. 流式响应不工作
- 检查浏览器网络面板，看SSE请求是否正常
- 确认没有代理或防火墙拦截

## 文件结构

### 关键文件位置

**后端:**
- `agent_api/src/api/service.py` - FastAPI入口，JWT验证
- `agent_api/src/api/routers/agent.py` - AI聊天路由
- `agent_api/src/agents/agents.py` - Agent配置
- `agent_api/.env` - 环境变量配置

**前端:**
- `web/lib/api.ts` - API客户端，流式调用
- `web/hooks/use-chat.ts` - 聊天状态管理
- `web/components/chat/global-chat-shell.tsx` - 聊天UI
- `web/lib/auth.tsx` - 认证上下文

## 配置说明

### JWT公钥配置
后端 `.env` 文件中的 `JWT_PUBLIC_KEY` 必须与 Casdoor 的公钥匹配：

```bash
# 从Casdoor获取公钥
curl http://localhost:8000/.well-known/jwks

# 转换为PEM格式并填入.env
JWT_PUBLIC_KEY="-----BEGIN PUBLIC KEY-----\n...\n-----END PUBLIC KEY-----"
```

### API URL配置
前端 `.env.local` 文件（如果不存在则创建）：
```bash
NEXT_PUBLIC_API_URL=http://localhost:8001
```

## 安全说明

- JWT使用RS256算法，后端只验证不签发
- Token由Casdoor（端口8000）签发
- 所有AI聊天接口都需要有效JWT
- 匿名用户会收到401错误

## 已完成的修复

1. ✅ 修复了JWT audience验证问题（禁用audience验证以支持多client）
2. ✅ 后端服务已重启应用配置
3. ✅ 基础设施检查通过
