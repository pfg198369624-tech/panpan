# App Review Insights - 开发需求文档

## 1. 项目概述

### 1.1 项目背景

构建一个可运行的 Web 工具，用户输入美区 App Store 链接和分析目标，系统自动完成：
采集评论 → 清洗去重 → AI 动态分类分析 → 证据评估 → PRD 生成 → 测试用例生成 → 追溯链验证，并在 UI 中展示完整流程和交付物。

### 1.2 核心目标

- 输入：App Store URL + 分析目标（如订阅转化/可用性/低分评论等）
- 输出：结构化 PRD（多版本规划）+ 可追溯的测试用例
- 全流程 AI 驱动（火山方舟豆包模型），不依赖 App 硬编码
- 支持 JSON/CSV 导入和缓存数据标注

### 1.3 技术栈

| 层次 | 技术 |
|------|------|
| 前端 | Vue 3 + Element Plus + Vite + Pinia + Vue Router |
| 后端 | Python FastAPI + SQLAlchemy + Celery (可选异步) |
| 数据库 | MySQL 8.0 |
| AI | 火山方舟（豆包模型）API |
| 数据采集 | iTunes RSS Feed API |

---

## 2. 系统架构

```
┌──────────────────────────────────────────────────────────────────┐
│                    前端 (Vue3 + Element Plus)                     │
│  Home │ Workflow │ Reviews │ Analysis │ PRD │ Cases │ DataSource│
└───────────────────────────┬──────────────────────────────────────┘
                            │ HTTP / WebSocket
┌───────────────────────────▼──────────────────────────────────────┐
│                      FastAPI 后端                                 │
│                                                                  │
│  ┌──────────┐  ┌────────┐  ┌──────────┐  ┌──────────────────┐  │
│  │ Collector│→│ Cleaner │→│Classifier │→│ Analyzer         │  │
│  └──────────┘  └────────┘  └──────────┘  └───────┬──────────┘  │
│                                                   ▼             │
│  ┌──────────┐  ┌────────┐  ┌──────────┐  ┌──────────────────┐  │
│  │Validator │← │TestGen │← │PRDGen    │← │ EvidenceEvaluator│  │
│  └──────────┘  └────────┘  └──────────┘  └──────────────────┘  │
│                                                   ▲             │
│  ┌───────────────────────────────────────────────┴──────────┐  │
│  │   ReflectionEngine (反思/重分析/闭环重试)                │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                  │
│  ┌──────────┐  ┌─────────────┐  ┌──────────────┐  ┌─────────┐  │
│  │Importer  │  │CacheManager │  │AIClient(方舟)│  │Monitor  │  │
│  └──────────┘  └─────────────┘  └──────┬───────┘  └─────────┘  │
│                                        │                        │
│  ┌──────────────┐  ┌──────────────────┐│                        │
│  │ConfigCenter  │  │PromptManager     ││                        │
│  └──────────────┘  └──────────────────┘│                        │
│                                        ▼                        │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │            AISchemaValidator (Pydantic + JSON校验+修复)  │   │
│  └──────────────────────────────────────────────────────────┘   │
└───────────────────────────┬──────────────────────────────────────┘
                            │
┌───────────────────────────▼──────────────────────────────────────┐
│                      MySQL 8.0                                    │
│  analysis_sessions  (会话追踪/状态/模型/耗时/Token/成本)         │
│  reviews_raw │ reviews_cleaned │ classifications │ findings      │
│  prd_requirements │ prd_versions │ test_cases │ workflow_logs   │
│  ai_call_logs     (调用监控/Token/失败/重试)                     │
└──────────────────────────────────────────────────────────────────┘
```

---

## 3. 数据库设计 (MySQL 8.0 DDL)

### 3.1 reviews_raw — 原始评论

```sql
CREATE TABLE reviews_raw (
    id            BIGINT AUTO_INCREMENT PRIMARY KEY,
    app_id        VARCHAR(64) NOT NULL COMMENT 'App ID',
    review_id     VARCHAR(128) NOT NULL UNIQUE COMMENT 'Apple 评论唯一ID',
    author        VARCHAR(255),
    rating        TINYINT NOT NULL COMMENT '1-5 分',
    title         TEXT,
    content       TEXT NOT NULL,
    version       VARCHAR(64) COMMENT '用户填写的 App 版本',
    country       VARCHAR(8) DEFAULT 'us',
    reviewed_at   DATETIME COMMENT '评论时间',
    collected_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
    source        VARCHAR(32) DEFAULT 'rss' COMMENT 'rss / import_json / import_csv',
    INDEX idx_app_id (app_id)
);
```

### 3.2 reviews_cleaned — 清洗后评论

```sql
CREATE TABLE reviews_cleaned (
    id              BIGINT AUTO_INCREMENT PRIMARY KEY,
    raw_id          BIGINT NOT NULL UNIQUE,
    content_clean   TEXT COMMENT '清洗后文本',
    language        VARCHAR(16) COMMENT '检测语言',
    is_duplicate    TINYINT DEFAULT 0 COMMENT '是否重复',
    duplicate_group VARCHAR(64) COMMENT '重复组标识',
    is_noise        TINYINT DEFAULT 0 COMMENT '是否噪音(无意义评论)',
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (raw_id) REFERENCES reviews_raw(id)
);
```

### 3.3 classifications — 分类结果

```sql
CREATE TABLE classifications (
    id              BIGINT AUTO_INCREMENT PRIMARY KEY,
    cleaned_id      BIGINT NOT NULL,
    topic           VARCHAR(128) NOT NULL COMMENT '动态主题',
    subtopic        VARCHAR(128),
    sentiment       VARCHAR(16) COMMENT 'positive/negative/neutral',
    ai_labeled      TINYINT DEFAULT 1 COMMENT '是否AI标注',
    confidence      DECIMAL(5,2) COMMENT 'AI置信度',
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (cleaned_id) REFERENCES reviews_cleaned(id),
    INDEX idx_topic (topic)
);
```

### 3.4 findings — 分析发现

```sql
CREATE TABLE findings (
    id                   BIGINT AUTO_INCREMENT PRIMARY KEY,
    title                VARCHAR(255) NOT NULL COMMENT '发现标题',
    description          TEXT COMMENT '详细描述',
    source_review_ids    JSON COMMENT '来源评论ID列表',
    sample_count         INT DEFAULT 0 COMMENT '支持样本数',
    confidence           VARCHAR(32) COMMENT 'high / medium / low / uncertain',
    conflicting_evidence TEXT COMMENT '矛盾证据说明',
    conclusion_type      VARCHAR(32) COMMENT 'model / deterministic / assumption',
    is_confirmed         TINYINT DEFAULT 0 COMMENT '是否经验证',
    created_at           DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

### 3.5 prd_versions — 版本规划

```sql
CREATE TABLE prd_versions (
    id          BIGINT AUTO_INCREMENT PRIMARY KEY,
    version_no  VARCHAR(32) NOT NULL COMMENT '版本号 (v1.0 / v2.0)',
    name        VARCHAR(128) COMMENT '版本名称',
    priority    INT DEFAULT 0 COMMENT '优先级排序',
    status      VARCHAR(32) DEFAULT 'planned' COMMENT 'planned / in_progress / done',
    created_at  DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

### 3.6 prd_requirements — PRD 需求

```sql
CREATE TABLE prd_requirements (
    id              BIGINT AUTO_INCREMENT PRIMARY KEY,
    version_id      BIGINT NOT NULL,
    req_id          VARCHAR(32) NOT NULL UNIQUE COMMENT '需求编号 REQ-001',
    title           VARCHAR(255) NOT NULL,
    description     TEXT,
    priority        VARCHAR(16) DEFAULT 'medium' COMMENT 'P0/P1/P2',
    source_finding_ids JSON COMMENT '关联 finding ID 列表',
    status          VARCHAR(32) DEFAULT 'draft',
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (version_id) REFERENCES prd_versions(id)
);
```

### 3.7 test_cases — 测试用例

```sql
CREATE TABLE test_cases (
    id              BIGINT AUTO_INCREMENT PRIMARY KEY,
    case_id         VARCHAR(32) NOT NULL UNIQUE COMMENT 'TC-001',
    req_id          VARCHAR(32) NOT NULL COMMENT '关联需求编号',
    title           VARCHAR(255) NOT NULL,
    preconditions   TEXT,
    steps           JSON COMMENT '测试步骤数组',
    expected_result TEXT,
    source_review_ids JSON COMMENT '关联原始评论ID',
    status          VARCHAR(32) DEFAULT 'draft',
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

### 3.8 workflow_logs — 工作流日志

```sql
CREATE TABLE workflow_logs (
    id              BIGINT AUTO_INCREMENT PRIMARY KEY,
    session_id      VARCHAR(64) NOT NULL,
    step            VARCHAR(64) NOT NULL COMMENT '步骤名称',
    status          VARCHAR(32) COMMENT 'running / success / failed / revised / reflection',
    input_summary   TEXT,
    output_summary  TEXT,
    error_message   TEXT,
    started_at      DATETIME,
    finished_at     DATETIME,
    INDEX idx_session (session_id)
);
```

### 3.9 analysis_sessions — 分析会话（新增）

```sql
CREATE TABLE analysis_sessions (
    id                  VARCHAR(64) PRIMARY KEY COMMENT 'UUID 会话ID',
    app_id              VARCHAR(64) NOT NULL,
    app_name            VARCHAR(255),
    app_url             TEXT NOT NULL,
    user_goal           TEXT COMMENT '用户输入的分析目标',
    status              VARCHAR(32) DEFAULT 'created' COMMENT 'created/running/success/failed',
    current_step        INT DEFAULT 0 COMMENT '当前执行到第几步',
    ai_model            VARCHAR(128) COMMENT '使用的模型标识',
    total_tokens        INT DEFAULT 0 COMMENT '总Token消耗',
    total_cost          DECIMAL(10,6) DEFAULT 0 COMMENT '总成本(USD)',
    total_prompt_tokens INT DEFAULT 0,
    total_completion_tokens INT DEFAULT 0,
    ai_call_count       INT DEFAULT 0 COMMENT 'AI调用次数',
    ai_fail_count       INT DEFAULT 0 COMMENT 'AI失败次数',
    ai_retry_count      INT DEFAULT 0 COMMENT 'AI重试次数',
    started_at          DATETIME,
    finished_at         DATETIME,
    duration_seconds    INT DEFAULT 0 COMMENT '总耗时',
    error_message       TEXT,
    created_at          DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at          DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);
```

### 3.10 ai_call_logs — AI 调用日志（新增）

```sql
CREATE TABLE ai_call_logs (
    id              BIGINT AUTO_INCREMENT PRIMARY KEY,
    session_id      VARCHAR(64) NOT NULL,
    step            VARCHAR(64) COMMENT '所属步骤',
    task            VARCHAR(64) COMMENT '任务类型: classify/analyze/evaluate/prd/test/validate',
    model           VARCHAR(128),
    prompt_snapshot TEXT COMMENT '实际发送的prompt(可用于复现)',
    response_snapshot TEXT COMMENT '模型原始响应',
    prompt_tokens   INT DEFAULT 0,
    completion_tokens INT DEFAULT 0,
    total_tokens    INT DEFAULT 0,
    cost            DECIMAL(10,6) DEFAULT 0,
    status          VARCHAR(32) COMMENT 'success/failed/retry',
    error_message   TEXT,
    retry_count     INT DEFAULT 0,
    duration_ms     INT DEFAULT 0,
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_session (session_id),
    INDEX idx_task (task)
);
```

---

## 4. 后端模块详细设计

### 4.1 模块总览

| 模块 | 文件 | 类型 | AI参与 |
|------|------|------|--------|
| AIClient | `services/ai_client.py` | 基础设施 | - |
| AISchemaValidator | `schemas/ai_output.py` | 基础设施 | - |
| ConfigCenter | `core/config.py` | 基础设施 | - |
| PromptManager | `core/prompt_manager.py` | 基础设施 | - |
| MonitoringService | `services/monitor.py` | 基础设施 | - |
| Collector | `services/collector.py` | 确定性规则 | 否 |
| Importer | `services/importer.py` | 确定性规则 | 否 |
| CacheManager | `services/cache_manager.py` | 规则 | 否 |
| Cleaner | `services/cleaner.py` | 规则+AI | 豆包辅助清洗 |
| Classifier | `services/classifier.py` | AI驱动 | 豆包核心驱动 |
| Analyzer | `services/analyzer.py` | AI驱动 | 豆包核心驱动 |
| EvidenceEvaluator | `services/ev_evaluator.py` | AI驱动 | 豆包核心驱动 |
| PRDGenerator | `services/prd_generator.py` | AI驱动 | 豆包核心驱动 |
| TestGenerator | `services/test_generator.py` | AI驱动 | 豆包核心驱动 |
| Validator | `services/validator.py` | 规则+AI | 豆包辅助 |
| ReflectionEngine | `workflow/reflection.py` | Agent | 豆包辅助反思 |
| WorkflowEngine | `workflow/engine.py` | Agent编排 | 否 |

### 4.2 AIClient (ai_client.py)

```python
# 火山方舟 API 封装
# 功能:
#   - 统一调用豆包模型 chat/completions
#   - 自动重试 (指数退避, 最多3次)
#   - Token 用量统计
#   - 超时控制 (60s)
#   - 响应解析与错误分类
#
# 配置项 (.env):
#   VOLC_ACCESS_KEY=xxx
#   VOLC_SECRET_KEY=xxx
#   VOLC_MODEL_ENDPOINT=xxx  # 豆包模型 endpoint
#   AI_TIMEOUT=60
#   AI_MAX_RETRIES=3
```

### 4.3 Collector (collector.py)

```
输入: app_id (从 URL 提取)
输出: reviews_raw 表记录

流程:
1. 从 URL 解析 app_id
   - 正则提取 /id(\d+) 或 ?id=(\d+)
2. 调用 iTunes RSS Feed API:
   GET https://itunes.apple.com/rss/customerreviews/id={appId}/page={page}/sortby=mostrecent/json
3. 分页采集 (每页50条, 最多10页 = 500条)
4. 逐条写入 reviews_raw
5. Rate limiter: 每请求间隔 1s

限制说明:
- iTunes RSS Feed 最多返回 500 条评论
- 只有美国区数据
- 采集结果在 UI 中展示数据量说明
```

### 4.4 Importer (importer.py)

```
输入: JSON 或 CSV 文件上传
输出: reviews_raw 表记录

支持的导入格式:

JSON:
[
  {
    "review_id": "xxx",
    "author": "user1",
    "rating": 1,
    "title": "Bad app",
    "content": "It crashes all the time",
    "version": "3.2.1",
    "reviewed_at": "2024-01-15T10:30:00Z"
  }
]

CSV:
review_id,author,rating,title,content,version,reviewed_at

导入后 source 字段标记为 import_json / import_csv
```

### 4.5 CacheManager (cache_manager.py)

```
功能:
- 每次采集完成后可选保存缓存到 backend/cached_data/
- 缓存文件名: {app_id}_{timestamp}.json
- 缓存文件头部添加标注:
  {
    "__cache_meta__": {
      "app_id": "839285684",
      "collected_at": "2025-07-18T10:00:00Z",
      "source": "iTunes RSS Feed",
      "count": 500,
      "is_cached": true,
      "note": "此文件为缓存数据，仅在网络不可用时作为回退。在线模式下优先使用实时采集。"
    },
    "reviews": [...]
  }
- 在线模式下不使用缓存，缓存仅作为离线参考
- UI 中缓存数据标注 "⚠ 缓存数据" 标签
```

### 4.6 Cleaner (cleaner.py)

```
输入: reviews_raw 表记录
输出: reviews_cleaned 表记录

规则处理 (确定性):
1. 去除 HTML 标签
2. 去除首尾空白
3. 统一换行符
4. 检测语言 (langdetect)
5. 去重: 相同 review_id 或 content 相似度 > 95% (difflib) 标记为重复
6. 噪音过滤: 纯标点、纯数字、过短 (<3字符) 标记为噪音

AI 处理 (豆包 — 可选):
- 对难以确定的内容调用豆包判断是否为有意义评论
- Prompt: "判断以下 App Store 评论是否是有意义的用户反馈，返回 yes/no"
```

### 4.7 Classifier (classifier.py) — AI 核心

```
输入: reviews_cleaned 记录
输出: classifications 表记录

流程:
1. 将评论分批 (每批 20 条)
2. 调用豆包模型进行动态主题发现

Prompt 模板 (核心):
-----
你是一个 App Store 评论分析专家。请分析以下用户评论，执行:
1. 为每条评论分配一个动态主题 (topic) 和子主题 (subtopic)
2. 判断情感倾向 (positive/negative/neutral)
3. 给出置信度 (0-1)

注意: 不要使用预定义的分类体系，根据评论实际内容动态生成主题。
主题应该具体，例如 "订阅价格过高" 而不是 "价格问题"。

评论列表:
{reviews_json}

返回 JSON 格式:
[
  {"review_index": 0, "topic": "...", "subtopic": "...", "sentiment": "...", "confidence": 0.95},
  ...
]
-----

3. 对分类结果进行聚合统计，生成主题分布
4. 标记每个分类是否 AI 生成 (ai_labeled=1)
```

### 4.8 Analyzer (analyzer.py)

```
输入: classifications + reviews_cleaned
输出: 聚合分析报告 (内存)

流程:
1. 按 topic 分组统计评论数、平均评分
2. 调用豆包对每个主要 topic 进行深度分析

Prompt:
-----
以下是一组关于 "{topic}" 主题的用户评论 ({count}条)。
请分析用户核心问题是什么，并总结出关键发现。

评论:
{reviews_text}

输出 JSON:
{
  "core_problem": "用户核心问题描述",
  "key_findings": ["发现1", "发现2"],
  "severity": "high/medium/low"
}
-----
```

### 4.9 EvidenceEvaluator (ev_evaluator.py) — AI 核心

```
输入: 聚合分析报告
输出: findings 表记录

流程:
对每个潜在发现，评估:
1. 样本量是否足够 (规则: <3条标记为低置信度)
2. 是否存在矛盾评论 (AI检测)
3. 标记 confidence: high/medium/low/uncertain
4. 标记 conclusion_type: model/deterministic/assumption

Prompt:
-----
检查以下发现中是否存在矛盾的用户反馈，评估证据充分性:

主题: {topic}
支持评论: {supporting_reviews}
反对评论: {opposing_reviews}

输出 JSON:
{
  "evidence_sufficient": true/false,
  "conflicting_feedback": "矛盾描述或 null",
  "confidence": "high/medium/low/uncertain",
  "data_limitations": "数据局限性说明",
  "recommendation": "建议"
}
-----
```

### 4.10 PRDGenerator (prd_generator.py) — AI 核心

```
输入: findings 表记录
输出: prd_versions + prd_requirements 表记录

流程:
1. 调用豆包将 findings 转化为产品需求

Prompt:
-----
基于以下用户反馈分析发现，生成产品需求文档 (PRD):

发现列表:
{findings_json}

要求:
1. 每个需求必须有明确的边界描述
2. 按优先级分为 P0/P1/P2
3. 规划到多个版本中 (v1.0 MVP, v2.0 迭代)
4. 关联对应的 finding ID
5. 每个需求需引用支持该需求的用户评论 excerpt

输出 JSON:
{
  "versions": [
    {
      "version": "v1.0",
      "name": "MVP",
      "requirements": [
        {
          "req_id": "REQ-001",
          "title": "...",
          "description": "...",
          "priority": "P0",
          "source_finding_ids": [1, 2],
          "source_review_excerpts": ["..."]
        }
      ]
    }
  ]
}
-----

2. 写入 prd_versions 和 prd_requirements 表
```

### 4.11 TestGenerator (test_generator.py) — AI 核心

```
输入: prd_requirements
输出: test_cases 表记录

流程:
1. 对每个 PRD 需求，调用豆包生成测试用例

Prompt:
-----
基于以下产品需求生成测试用例:

需求: {req_title}
描述: {req_description}
关联用户评论: {source_reviews}

要求:
1. 测试用例必须能验证该需求是否解决了用户评论中提出的问题
2. 包含前置条件、测试步骤、预期结果
3. 关联到原始评论 ID

输出 JSON:
{
  "test_cases": [
    {
      "case_id": "TC-001",
      "title": "...",
      "preconditions": "...",
      "steps": ["步骤1", "步骤2"],
      "expected_result": "...",
      "source_review_ids": [1, 2, 3]
    }
  ]
}
-----

2. 写入 test_cases 表
```

### 4.12 Validator (validator.py)

```
输入: findings / prd_requirements / test_cases
输出: 验证报告

规则验证:
1. 每个 finding 必须有 source_review_ids (非空)
2. 每个 requirement 必须有 source_finding_ids (非空)
3. 每个 test_case 必须有 req_id 和 source_review_ids (非空)
4. 追溯链完整性: review → finding → requirement → test_case
5. 无来源支撑的结论标记为 assumption

AI 验证:
- 豆包检查 requirement 是否确实源自用户反馈
- 对 unsupported conclusions 给出修改建议

输出:
{
  "passed": true/false,
  "issues": [
    {
      "type": "missing_traceability",
      "entity_id": "REQ-003",
      "description": "此需求无关联的用户评论支撑",
      "suggestion": "..."
    }
  ],
  "revisions": [...]
}
```

### 4.13 WorkflowEngine (workflow/engine.py) — Agent 模式

```
Agent 工作流编排，不再是线性执行，而是支持反思(Reflection)、闭环重试、证据不足重分析:

┌──────────────────────────────────────────────────────────────────┐
│  Agent Loop (每步都是一个智能体，独立决策)                        │
│                                                                  │
│  Step 1: ScopeDeterminationAgent                                 │
│    → 输出: scope (分析范围、目标拆解、数据需求)                   │
│    → 自我反思: "范围是否明确？是否需要用户补充？"                 │
│                                                                  │
│  Step 2: CollectionAgent                                         │
│    → 采集/导入 → raw                                             │
│    → 反思: "数据量是否足够？不足则尝试更多页面或提示用户导入"     │
│                                                                  │
│  Step 3: CleaningAgent                                           │
│    → 清洗去重 → cleaned                                          │
│    → 反思: "噪音比例是否过高？是否需要调整清洗阈值？"             │
│                                                                  │
│  Step 4: ClassificationAgent (豆包驱动)                          │
│    → 动态分类 → topics                                           │
│    → 反思: "分类粒度是否合理？主题是否过于分散或笼统？"          │
│    → 如不满意 → 调整Prompt参数 → 重新分类                        │
│                                                                  │
│  Step 5: EvidenceEvaluationAgent (豆包驱动)                      │
│    → 评估证据 → findings                                        │
│    → 反思: "是否有足够的证据支撑这些发现？是否存在矛盾？"        │
│    → 证据不足 → 标记为 assumption 或 回到 Step 2 补充数据       │
│                                                                  │
│  Step 6: PRDAgent (豆包驱动)                                     │
│    → 生成PRD → requirements                                     │
│    → 反思: "每个需求是否确实来源于用户反馈？边界是否清晰？"     │
│    → 需求无来源 → 标记 assumption 或 回到 Step 5 补充证据      │
│                                                                  │
│  Step 7: TestCaseAgent (豆包驱动)                                │
│    → 生成用例 → test_cases                                      │
│    → 反思: "用例能否验证对应的需求是否解决用户问题？"            │
│                                                                  │
│  Step 8: ValidationAgent (规则+AI)                               │
│    → 验证追溯链 → report                                        │
│    → 发现断裂 → 标记/删除/修改 → 通知前端                      │
│                                                                  │
│  Step 9: DisplayAgent                                           │
│    → 整理结果 → 推送至前端                                      │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘

反射(Reflection)机制:
- 每步执行后，Agent 审查自己的输出质量
- 自我提问: "这个结果合理吗？证据充分吗？有没有矛盾？"
- 通过/不通过 → 继续下一步 或 重新执行当前步(最多3次)
- 反射结果记录到 workflow_logs (status=reflection)

闭环重试(Retry)策略:
- AI 调用失败: 指数退避 (1s, 2s, 4s) 最多3次
- 步骤验证不通过: 最多重试2次，每次调整 Prompt 参数
- 重试耗尽: 跳过该步，标记为 failed，在 UI 中标注

状态同步:
- 每步开始/结束/反思/重试通过 WebSocket 推送到前端
- 中间结果和 Agent 思考过程存入 workflow_logs
```

### 4.14 ConfigCenter (core/config.py) — 配置中心

```
统一管理所有配置，支持环境变量覆盖:

配置项分类:
├── app: 应用基本配置 (APP_NAME, DEBUG, SECRET_KEY)
├── database: MySQL 连接 (DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD)
├── ai: 火山方舟配置 (VOLC_ACCESS_KEY, VOLC_SECRET_KEY, VOLC_MODEL_ENDPOINT)
│   ├── timeout: AI_TIMEOUT (默认60s)
│   ├── max_retries: AI_MAX_RETRIES (默认3)
│   └── model_params: temperature=0.3, max_tokens=4096
├── collection: 采集配置 (MAX_PAGES=10, PAGE_SIZE=50, RATE_LIMIT=1s)
├── workflow: 工作流配置 (MAX_REFLECTION_ROUNDS=3, MAX_RETRY_PER_STEP=2)
└── monitoring: 监控配置 (LOG_AI_CALLS=true, LOG_PROMPTS=true)

实现方式:
- Pydantic Settings (BaseSettings) 自动从 .env 读取
- 单例模式，全局可访问
- 敏感字段自动脱敏日志输出
```

### 4.15 MonitoringService (services/monitor.py) — 监控与成本统计

```
功能:
1. 记录每次 AI 调用的 Token/耗时/成本
2. 统计每个 Session 的总消耗
3. 记录失败率和重试率

核心方法:
- record_ai_call(session_id, task, model, prompt_tokens, completion_tokens, cost, status, duration_ms)
- get_session_stats(session_id) → {total_tokens, total_cost, call_count, fail_count, retry_count}
- get_session_call_logs(session_id) → ai_call_logs 列表
- get_summary_stats() → 全局汇总

写入表:
- ai_call_logs (每次AI调用一条记录)
- analysis_sessions (汇总统计)

UI 展示:
- Analysis 页底部展示 Token 消耗和成本统计
- 便于面试官评估 API 使用成本
```

### 4.16 AISchemaValidator (schemas/ai_output.py) — AI 输出校验与修复

```
功能:
1. 定义 Pydantic DTO Schema 约束 AI 输出结构
2. 对豆包返回的 JSON 进行 Schema 校验
3. 校验失败时自动修复 (JSON 容错解析)
4. 修复失败时触发重试

核心 Schema 定义:

class ClassificationOutput(BaseModel):
    review_index: int = Field(ge=0)
    topic: str = Field(min_length=1)
    subtopic: Optional[str] = None
    sentiment: Literal["positive", "negative", "neutral"]
    confidence: float = Field(ge=0, le=1)

class FindingOutput(BaseModel):
    evidence_sufficient: bool
    conflicting_feedback: Optional[str]
    confidence: Literal["high", "medium", "low", "uncertain"]
    data_limitations: Optional[str]
    recommendation: Optional[str]

class PRDVersionOutput(BaseModel):
    version: str
    name: str
    requirements: List[PRDRequirementOutput]

class PRDRequirementOutput(BaseModel):
    req_id: str
    title: str = Field(min_length=1)
    description: str
    priority: Literal["P0", "P1", "P2"]
    source_finding_ids: List[int] = Field(min_length=1)
    source_review_excerpts: List[str]

class TestCaseOutput(BaseModel):
    case_id: str
    title: str
    preconditions: str
    steps: List[str] = Field(min_length=1)
    expected_result: str
    source_review_ids: List[int]

自动修复策略:
1. 尝试 json.loads() 直接解析
2. 失败 → 尝试修复常见错误 (单引号换双引号、尾逗号删除、截断补齐)
3. 修复后再次校验 Schema
4. 仍失败 → 返回 None，触发上层重试

使用位置:
- 所有调用豆包的地方，先用 Schema 校验再写入数据库
- 校验失败时写入 ai_call_logs 的 error_message
```

---

## 5. API 接口设计

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/workflow/start` | 启动分析工作流 |
| GET | `/api/workflow/{session_id}/status` | 获取工作流状态 |
| GET | `/api/workflow/{session_id}/logs` | 获取工作流日志 |
| GET | `/api/workflow/{session_id}/session` | 获取会话详情 (含Token/成本统计) |
| POST | `/api/import/json` | 导入 JSON 评论文件 |
| POST | `/api/import/csv` | 导入 CSV 评论文件 |
| GET | `/api/reviews/raw?session_id=` | 获取原始评论 |
| GET | `/api/reviews/cleaned?session_id=` | 获取清洗后评论 |
| GET | `/api/classifications?session_id=` | 获取分类结果 |
| GET | `/api/findings?session_id=` | 获取分析发现 |
| GET | `/api/prd/versions?session_id=` | 获取版本规划 |
| GET | `/api/prd/requirements?session_id=` | 获取需求列表 |
| GET | `/api/test-cases?session_id=` | 获取测试用例 |
| GET | `/api/validation/report?session_id=` | 获取追溯验证报告 |
| GET | `/api/analysis/scope?session_id=` | 获取分析范围说明 |
| GET | `/api/data-source/info` | 获取数据源说明 |
| GET | `/api/monitor/stats?session_id=` | 获取监控统计 (Token/成本/失败率) |
| GET | `/api/monitor/call-logs?session_id=` | 获取 AI 调用日志列表 |

---

## 6. 前端页面设计

### 6.1 路由

| 路径 | 页面 | 说明 |
|------|------|------|
| `/` | Home.vue | 输入 URL + 分析目标 + 启动按钮 + 文件导入 |
| `/workflow/:session_id` | Workflow.vue | 工作流进度展示 (WebSocket) |
| `/reviews/:session_id` | Reviews.vue | 原始 / 清洗后评论切换 |
| `/analysis/:session_id` | Analysis.vue | 分类 + 发现 + 证据评估 |
| `/prd/:session_id` | PRD.vue | 版本规划 + 需求列表 |
| `/test-cases/:session_id` | TestCases.vue | 测试用例 (可追溯) |
| `/data-source` | DataSource.vue | 数据源说明 + 缓存标注 |

### 6.2 组件树

```
App.vue
├── Layout.vue (侧边栏 + 顶栏)
│   ├── Home.vue
│   │   ├── UrlInput.vue        # URL 输入框
│   │   ├── GoalInput.vue       # 分析目标输入
│   │   ├── ImportUploader.vue  # 文件导入
│   │   └── StartButton.vue     # 启动按钮
│   ├── Workflow.vue
│   │   ├── StepTimeline.vue    # 9 步时间线
│   │   ├── StepDetail.vue      # 当前步骤详情
│   │   └── LogPanel.vue        # 日志面板
│   ├── Reviews.vue
│   │   ├── DataSourceBanner.vue # 数据源标注 + 缓存标注
│   │   ├── ReviewTable.vue     # 评论表格
│   │   └── ReviewStats.vue     # 统计概览
│   ├── Analysis.vue
│   │   ├── TopicDistribution.vue # 主题分布图
│   │   ├── FindingCard.vue     # 发现卡片 (含置信度/矛盾证据)
│   │   └── EvidenceBadge.vue   # 证据标记组件
│   ├── PRD.vue
│   │   ├── VersionTabs.vue     # 版本 Tab
│   │   └── RequirementCard.vue # 需求卡片 (含追溯链)
│   ├── TestCases.vue
│   │   └── TestCaseCard.vue    # 用例卡片 (含追溯链)
│   └── DataSource.vue
│       ├── SourceExplanation.vue
│       └── CacheIndicator.vue
```

### 6.3 页面核心功能要求

**Home 页**:
- URL 输入框 (预填示例: `https://apps.apple.com/us/app/workout-for-women-home-gym/id839285684`)
- 分析目标输入 (可选，示例: "关注订阅转化问题" / "分析低分评论原因")
- 文件导入按钮 (JSON/CSV)
- 历史会话列表
- 点击启动后跳转到 Workflow 页

**Workflow 页 (关键)**:
- 垂直时间线展示 9 步进度
- 每步显示: 图标(运行中/成功/失败/修订)、步骤名、耗时
- 当前步骤展开显示详细日志
- WebSocket 实时推送状态

**Analysis 页**:
- 主题分布 (柱状图 / 词云)
- Findings 卡片列表，每张卡片显示:
  - 标题
  - 支持样本数
  - 置信度标签 (high/medium/low/uncertain) + 颜色区分
  - 结论类型标签 (model/deterministic/assumption)
  - 矛盾证据展示 (如有)
  - 来源评论 excerpt (可点击展开)

**PRD 页**:
- 多版本 Tab 切换
- 每个需求卡片显示: 编号、标题、优先级(P0红/P1黄/P2灰)、关联 finding、来源评论 excerpt

**TestCases 页**:
- 每个用例显示: 编号、关联需求、步骤、预期结果、来源评论链接

---

## 7. AI 集成设计

### 7.1 火山方舟配置

```env
VOLC_ACCESS_KEY=your_access_key
VOLC_SECRET_KEY=your_secret_key
VOLC_MODEL_ENDPOINT=your_doubao_endpoint
AI_TIMEOUT=60
AI_MAX_RETRIES=3
```

### 7.2 调用策略

| 任务 | 模型 | 调用方式 | 超时 | 重试 |
|------|------|----------|------|------|
| 文本清洗辅助 | 豆包 | 单条判断 | 15s | 2次 |
| 动态分类 | 豆包 | 批处理 (20条/批) | 60s | 3次 |
| 深度分析 | 豆包 | 单次调用 | 60s | 3次 |
| 证据评估 | 豆包 | 单次调用 | 60s | 3次 |
| PRD 生成 | 豆包 | 单次调用 | 120s | 3次 |
| 测试用例生成 | 豆包 | 单次调用 | 120s | 3次 |
| 追溯验证 | 豆包 | 单次调用 | 60s | 2次 |

### 7.3 防幻觉措施

1. 所有 AI 调用必须传入具体数据，禁止凭空生成
2. Prompt 明确要求: "如果数据不足以得出结论，请如实说明，不要编造"
3. 每次 AI 输出后校验 JSON 完整性
4. findings 中 conclusion_type=assumption 标记无数据支撑的推论
5. 追溯链验证: 任何无法链接到原始评论的输出被标记或删除

### 7.4 失败处理

```
AI 调用失败 → 重试 (指数退避: 1s, 2s, 4s)
重试仍失败 → 降级策略:
  - 分类: 回退到基于评分的关键词规则
  - 分析: 跳过深度分析，仅展示统计数据
  - PRD: 无法自动生成，提示用户手动输入
  - 测试用例: 同上
失败记录 → 写入 workflow_logs 并在 UI 中展示
```

### 7.5 Prompt 版本管理

```
统一管理所有 Prompt，支持版本迭代:

目录结构:
backend/prompts/
├── __init__.py
├── classifier/
│   ├── v1.md              # 初始版本
│   └── v2.md              # 迭代版本(优化后)
├── analyzer/
│   ├── v1.md
│   └── ...
├── evaluator/
│   └── v1.md
├── prd_generator/
│   └── v1.md
├── test_generator/
│   └── v1.md
└── validator/
    └── v1.md

管理方式:
- PromptManager 统一加载，支持版本号参数
- Prompt 内容包含参数占位符: {{reviews_json}}, {{findings_json}}, {{topic}}
- 每个 Prompt 文件头部包含元数据:
  ---
  model: doubao
  temperature: 0.3
  max_tokens: 4096
  version: v1
  description: 动态分类 Prompt
  ---
- 切换版本无需修改代码，只需修改配置:
  PROMPT_VERSION_CLASSIFIER=v2
```

### 7.6 监控与成本统计

```
监控指标:
├── Token 消耗: prompt_tokens + completion_tokens = total_tokens
├── 成本估算: 按豆包模型单价计算 (可配置)
├── 调用次数: ai_call_count (按 session + 按 task 维度)
├── 失败率: ai_fail_count / ai_call_count
├── 重试率: ai_retry_count / ai_call_count
├── 平均耗时: 每次调用的 duration_ms
└── 模型响应大小: response_snapshot 长度

数据来源:
- ai_call_logs 表 (每次AI调用一条记录)
- analysis_sessions 表 (汇总统计)

前端展示:
- Analysis 页底部增加 "分析成本" 面板
- 展示: 总Token/总成本/调用次数/失败率
- 每步调用的明细列表 (可展开)
```

### 7.7 AI 输出 Schema 校验（集成到调用链路）

```
每次 AI 调用后的处理管道:

AI 响应 (原始文本)
    │
    ▼
Step 1: JSON 解析
    ├── 成功 → Step 2
    └── 失败 → 自动修复
                ├── 修复成功 → Step 2
                └── 修复失败 → 返回 None → 触发重试

Step 2: Pydantic Schema 校验
    ├── 通过 → 写入数据库
    └── 不通过 → 提取校验错误
                   ├── 可自动修复(类型转换/默认值) → 写入数据库 + 日志标记
                   └── 不可修复 → 返回 None → 触发重试

使用 4.16 节定义的 Schema: ClassificationOutput / FindingOutput / ...
```

---

## 8. 异常场景处理

| 场景 | 处理方式 |
|------|----------|
| 网络不可用 (采集失败) | 检查缓存，如无缓存则提示用户导入文件 |
| 评论数据不足 (<10条) | 在 findings 中标注"样本量有限"，降低置信度 |
| 多语言评论 | langdetect 检测语言，分类时传给豆包处理 |
| 重复评论 | cleaner 中 difflib 相似度检测，标记去重 |
| 矛盾反馈 | ev_evaluator 中 AI 检测，在 finding 中展示 |
| AI 模型超时/失败 | 重试3次后降级回退，日志记录 |
| 无效 App Store 链接 | 前端 URL 校验，后端正则提取 appId |
| 非美区链接 | 提示用户使用美区链接 |

---

## 9. 数据源与缓存说明

### 9.1 数据来源

- **主要**: Apple iTunes RSS Feed API (官方接口)
  - 端点: `https://itunes.apple.com/rss/customerreviews/id={appId}/page={page}/sortby=mostrecent/json`
  - 限制: 最多返回 500 条评论，仅美区 App Store
  - 优势: 官方接口，结构化 JSON，无需爬虫
- **次要**: 用户 JSON/CSV 文件导入
  - 用于离线场景或补充数据

### 9.2 缓存策略

```
cached_data/
├── 839285684_20250718_100000.json   # 缓存文件
└── README.md                        # 缓存说明
```

- 缓存文件头部包含 `__cache_meta__` 元数据标注
- UI 中使用缓存时显示 "⚠ 缓存数据 (采集于 xxxx-xx-xx)" 标签
- 在线模式不自动使用缓存，只作为离线回退

---

## 10. 开发阶段规划

| 阶段 | 内容 | 预估 |
|------|------|------|
| **Phase 1** | 项目脚手架 + 目录结构 + 数据库 DDL + 基本 API 框架 | 1天 |
| **Phase 2** | ConfigCenter + AIClient + AISchemaValidator + PromptManager + MonitoringService | 1天 |
| **Phase 3** | Collector + Importer + CacheManager + Cleaner | 1天 |
| **Phase 4** | Classifier + Analyzer (Prompt v1 设计 + Schema 定义) | 1.5天 |
| **Phase 5** | EvEvaluator + PRDGenerator + TestGenerator (含 Prompt v1) | 1.5天 |
| **Phase 6** | Validator + ReflectionEngine + WorkflowEngine + WebSocket 推送 | 1天 |
| **Phase 7** | 前端全部页面 (Vue3 + Element Plus + 监控面板) | 2天 |
| **Phase 8** | 端到端联调 + 异常场景处理 + 缓存标注 + 成本展示 | 1天 |
| **Phase 9** | 文档完善 + .env.example + 缓存数据生成 + Prompt 归档 | 0.5天 |
| **Total** | | ~10.5天 |

---

## 11. 附录: 需求文档追溯矩阵

| README 需求 | 覆盖模块 | 验证方式 |
|-------------|----------|----------|
| 9 步工作流自动执行 | WorkflowEngine + 各模块 | 端到端测试 |
| 用户输入 URL + 目标 | Home.vue → Collector | UI 测试 |
| 无 App 硬编码 | 所有 Prompt 通用 | 代码审查 |
| AI 模型驱动语义分析 | Classifier / Analyzer / PRDGen / TestGen | 单元测试 |
| 确定性规则场景 | Collector / Cleaner / Validator | 单元测试 |
| Finding 含来源/样本/置信度 | Analyzer + findings 表结构 | 数据校验 |
| 模型结论区分统计结论 | finding.conclusion_type | 数据校验 |
| JSON/CSV 导入 | Importer + ImportUploader | 功能测试 |
| 缓存标注 | CacheManager + DataSourceBanner | UI 测试 |
| 数据源说明 | DataSource.vue | UI 测试 |
| 频率限制 | Collector rate limiter | 代码审计 |
| 追溯链验证 | Validator | 集成测试 |
| 异常/失败/数据不足处理 | 各模块降级逻辑 | 场景测试 |
| 不编造数据 | Prompt 约束 + Validator | 代码审计 |
| 会话追踪 (Token/成本/耗时) | analysis_sessions + ai_call_logs + Monitor | 数据校验 |
| AI 输出格式校验与修复 | AISchemaValidator (Pydantic) | 单元测试 |
| Prompt 版本管理 | PromptManager + prompts/ 目录 | 代码审查 |
| Agent 反思/闭环重试 | ReflectionEngine + WorkflowEngine | 集成测试 |
| 配置中心 | ConfigCenter (Pydantic Settings) | 单元测试 |

## 12. 工程目录结构

```
app-review-insights/
│
├── frontend/                         # Vue3 + Vite 前端
│   ├── src/
│   │   ├── api/                      # API 封装
│   │   │   ├── workflow.ts
│   │   │   ├── reviews.ts
│   │   │   ├── analysis.ts
│   │   │   ├── prd.ts
│   │   │   ├── testCases.ts
│   │   │   └── monitor.ts
│   │   ├── components/               # 通用组件
│   │   │   ├── SessionCard.vue
│   │   │   ├── EvidenceBadge.vue
│   │   │   ├── ConfidenceTag.vue
│   │   │   └── CostPanel.vue
│   │   ├── views/                    # 页面
│   │   │   ├── Home.vue
│   │   │   ├── Workflow.vue
│   │   │   ├── Reviews.vue
│   │   │   ├── Analysis.vue
│   │   │   ├── PRD.vue
│   │   │   ├── TestCases.vue
│   │   │   └── DataSource.vue
│   │   ├── stores/                   # Pinia 状态
│   │   │   └── session.ts
│   │   ├── router/
│   │   │   └── index.ts
│   │   └── App.vue
│   ├── package.json
│   └── vite.config.ts
│
├── backend/                          # Python FastAPI 后端
│   ├── app/
│   │   ├── __init__.py
│   │   │
│   │   ├── api/                      # API 路由层
│   │   │   ├── __init__.py
│   │   │   ├── workflow.py
│   │   │   ├── reviews.py
│   │   │   ├── analysis.py
│   │   │   ├── prd.py
│   │   │   ├── test_cases.py
│   │   │   ├── import_api.py
│   │   │   └── monitor.py
│   │   │
│   │   ├── core/                     # 核心基础设施
│   │   │   ├── __init__.py
│   │   │   ├── config.py            # ConfigCenter (Pydantic Settings)
│   │   │   ├── database.py          # 数据库连接
│   │   │   ├── prompt_manager.py    # Prompt 版本管理
│   │   │   └── exceptions.py        # 自定义异常
│   │   │
│   │   ├── models/                   # SQLAlchemy ORM 模型 (数据层)
│   │   │   ├── __init__.py
│   │   │   ├── session.py           # analysis_sessions
│   │   │   ├── review.py            # reviews_raw + reviews_cleaned
│   │   │   ├── classification.py    # classifications
│   │   │   ├── finding.py           # findings
│   │   │   ├── prd.py               # prd_versions + prd_requirements
│   │   │   ├── test_case.py         # test_cases
│   │   │   ├── workflow_log.py      # workflow_logs
│   │   │   └── ai_call_log.py       # ai_call_logs
│   │   │
│   │   ├── schemas/                  # Pydantic DTO (校验层)
│   │   │   ├── __init__.py
│   │   │   ├── ai_output.py         # AI 输出 Schema + 自动修复
│   │   │   ├── api_request.py       # 请求 DTO
│   │   │   └── api_response.py      # 响应 DTO
│   │   │
│   │   ├── repositories/            # 数据访问层 (DAO)
│   │   │   ├── __init__.py
│   │   │   ├── session_repo.py
│   │   │   ├── review_repo.py
│   │   │   ├── classification_repo.py
│   │   │   ├── finding_repo.py
│   │   │   ├── prd_repo.py
│   │   │   ├── test_case_repo.py
│   │   │   └── monitor_repo.py
│   │   │
│   │   ├── services/                 # 业务逻辑层
│   │   │   ├── __init__.py
│   │   │   ├── ai_client.py         # 火山方舟 API 封装
│   │   │   ├── collector.py
│   │   │   ├── cleaner.py
│   │   │   ├── classifier.py
│   │   │   ├── analyzer.py
│   │   │   ├── ev_evaluator.py
│   │   │   ├── prd_generator.py
│   │   │   ├── test_generator.py
│   │   │   ├── validator.py
│   │   │   ├── importer.py
│   │   │   ├── cache_manager.py
│   │   │   └── monitor.py           # MonitoringService
│   │   │
│   │   └── workflow/                 # Agent 工作流层
│   │       ├── __init__.py
│   │       ├── engine.py            # WorkflowEngine (Agent编排)
│   │       ├── reflection.py        # ReflectionEngine (反思逻辑)
│   │       ├── steps.py             # 各步骤 Agent 定义
│   │       └── websocket.py         # WebSocket 推送
│   │
│   ├── prompts/                      # Prompt 版本管理
│   │   ├── classifier_v1.md
│   │   ├── analyzer_v1.md
│   │   ├── evaluator_v1.md
│   │   ├── prd_generator_v1.md
│   │   ├── test_generator_v1.md
│   │   └── validator_v1.md
│   │
│   ├── tests/                        # 测试
│   │   ├── test_collector.py
│   │   ├── test_cleaner.py
│   │   ├── test_classifier.py
│   │   ├── test_schema_validator.py
│   │   ├── test_workflow.py
│   │   └── ...
│   │
│   ├── cached_data/                  # 缓存数据 (带标注)
│   │   └── README.md                # 缓存说明
│   │
│   ├── requirements.txt
│   ├── .env.example
│   └── main.py                      # FastAPI 入口
│
├── database/                         # 数据库脚本
│   └── init.sql                     # 完整建表脚本
│
└── README.md                        # 项目说明
```
