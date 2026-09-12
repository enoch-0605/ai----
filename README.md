# 知关 AI MVP

基于 Taro + React + TypeScript 的微信小程序前端，以及 Python + FastAPI 的闯关后端。

## 当前范围

- 首页输入主题、选择 5/10 题和入门/进阶/专家难度
- 单选题、判断题和即时解析
- 连续答对/答错后的动态难度调整
- 分数、生命值、结果报告
- 匿名会话恢复和重复提交幂等
- Mock AI 默认可运行，DeepSeek 适配作为配置项

## 启动后端

```powershell
docker compose up -d mysql
python -m pip install -e "backend[test]"
Copy-Item backend/.env.example backend/.env
python -m uvicorn app.main:app --app-dir backend --reload --port 8000
```

`.env.example` 默认将 `STORAGE` 设为 `sqlalchemy`，会把会话快照保存到 Docker MySQL；不需要启动数据库时可改为 `STORAGE=memory`。

健康检查：`http://127.0.0.1:8000/api/v1/health`

运行测试：

```powershell
python -m pytest backend/tests -q
```

## 启动小程序

```powershell
npm install
npm run dev:weapp
```

将 `dist` 导入微信开发者工具。小程序请求地址默认是 `http://127.0.0.1:8000/api/v1`，真机调试时需要替换为 HTTPS 合法域名。

## DeepSeek 配置

当前默认 `AI_PROVIDER=mock`，便于本地测试。接入真实模型时，在后端环境变量中配置 `DEEPSEEK_API_KEY` 和 `DEEPSEEK_MODEL`，密钥不会进入小程序包。
