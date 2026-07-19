# App Review Insights 使用说明书

## 1. 环境要求

| 依赖 | 版本要求 |
|------|----------|
| Python | 3.10+ |
| Node.js | 18+ |
| MySQL | 8.0 |
| npm/yarn | 任意 |

## 2. 快速启动

### 2.1 数据库初始化

```sql
-- 创建数据库
CREATE DATABASE IF NOT EXISTS app_review_insights CHARACTER SET utf8mb4;

-- 执行建表脚本
source database/init.sql;
```

### 2.2 后端启动

```bash
cd backend

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑 .env，填入:
#   DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD
#   VOLC_ACCESS_KEY, VOLC_SECRET_KEY, VOLC_MODEL_ENDPOINT (AI 模型)
#   ITUNES_RSS_URL (采集地址，一般不用改)
#   COLLECTION_MAX_PAGES=1 (每会话最多采集几页，每页约20条)

# 启动服务
python -m uvicorn main:app --host 127.0.0.1 --port 8000
```

### 2.3 前端启动

```bash
cd frontend
npm install
npm run dev
# 浏览器打开 http://localhost:5173
```

## 3. 使用流程

### 3.1 标准分析流程

1. **打开首页** `http://localhost:5173`
2. **输入 App Store 链接**（示例已预填）
3. **可选：输入分析目标**（如"关注订阅转化问题"）
4. 点击 **"开始分析"**
5. 系统自动执行 7 步工作流：
   - 确定范围 → 采集评论 → 清洗去重 → AI 分类分析 → 生成 PRD → 生成测试用例 → 追溯验证
6. 完成后在侧边栏点击该会话，依次查看：
   - **评论**：原始/清洗后评论
   - **分析**：主题分布 + AI 发现（含置信度、矛盾证据）
   - **PRD**：多版本需求规划
   - **测试用例**：可追溯到用户评论的用例

### 3.2 文件导入模式

当网络不可用或需要补充数据时：

1. 首页点击 **文件导入** 区域
2. 选择 JSON 或 CSV 文件
3. 系统自动创建会话并运行完整工作流

**JSON 格式**：
```json
[
  {
    "review_id": "123",
    "author": "user1",
    "rating": 1,
    "title": "Bad app",
    "content": "It crashes all the time",
    "version": "3.2.1",
    "reviewed_at": "2024-01-15T10:30:00Z"
  }
]
```

**CSV 格式**：
```csv
review_id,author,rating,title,content,version,reviewed_at
123,user1,1,Bad app,It crashes all the time,3.2.1,2024-01-15T10:30:00Z
```

### 3.3 侧边栏操作

- 点击历史会话查看对应分析结果
- 每个会话显示 `Pn Tm`（PRD 需求数 / 测试用例数）
- 状态圆点：🟢 成功 🔴 失败 🟡 进行中 ⚪ 已创建

## 4. 配置说明

### 4.1 核心环境变量 (.env)

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `VOLC_ACCESS_KEY` | 火山方舟 Access Key | (必填) |
| `VOLC_SECRET_KEY` | 火山方舟 Secret Key | (必填) |
| `VOLC_MODEL_ENDPOINT` | 模型 Endpoint | (必填) |
| `AI_TIMEOUT` | AI 调用超时(秒) | `300` |
| `AI_MAX_TOKENS` | AI 最大输出 Token | `8192` |
| `COLLECTION_MAX_PAGES` | RSS 采集页数 | `1` |
| `ITUNES_RSS_URL` | RSS Feed URL 模板 | (见下) |

### 4.2 RSS 采集 URL 模板

```
https://itunes.apple.com/us/rss/customerreviews/page={page}/id={appId}/sortby=mostrecent/json?limit=20
```

参数说明：
- `{page}` — 页码（从 1 开始）
- `{appId}` — App Store ID（从 URL 自动提取）
- `?limit=20` — 每页返回条数

调整 `COLLECTION_MAX_PAGES` 控制每个会话的采集总量（`页数 × 20 条`）。

### 4.3 历史会话显示数量

后端 `backend/app/api/workflow.py:96` 的 `.limit(50)` 控制侧边栏显示多少个历史会话。

## 5. 关键限制

### 5.1 数据源

| 来源 | 说明 | 限制 |
|------|------|------|
| iTunes RSS Feed | Apple 官方接口，结构化 JSON | 约 40% 概率返回空；仅美区数据；不稳定 |
| 文件导入 | JSON / CSV | 需要用户自行准备数据 |
| 缓存文件 | `backend/cached_data/` 目录 | 仅离线回退，不作为主要数据源 |

### 5.2 RSS 不稳定处理

- 代码已内置每页 3 次重试
- 如持续失败，请在 UI 中使用 "文件导入" 功能
- 缓存数据（Workout for Women, 50 条）位于 `backend/cached_data/839285684_20260719.json`

### 5.3 其他 App 采集注意

只有 README 指定 App（Workout for Women Home Gym, id=839285684）的 RSS 有数据可采。其他 App（如 Asana、WhatsApp）RSS 通常返回空，建议使用文件导入模式。

## 6. 常见问题

**Q: 启动后端报数据库连接错误？**
检查 `.env` 中 `DB_HOST`、`DB_PORT`、`DB_USER`、`DB_PASSWORD` 是否正确，且 MySQL 服务已启动。

**Q: 开始分析后一直卡在步骤 1？**
查看后端终端日志。常见原因：AI 模型配置有误、网络无法访问火山方舟 API。

**Q: RSS 采集返回 0 条数据？**
已知问题，Apple RSS 端点不稳定。重试几次，或使用文件导入功能。

**Q: 前端请求后端跨域报错？**
确认后端运行在 `127.0.0.1:8000`，前端在 `localhost:5173`。后端已配置 CORS 允许该来源。

**Q: 如何调整 AI 模型参数？**
编辑 `.env` 中的 `AI_TIMEOUT`（超时）和 `AI_MAX_TOKENS`（最大输出长度），或修改 `backend/app/core/config.py`。
