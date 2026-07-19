---
model: doubao
temperature: 0.3
max_tokens: 8192
version: v1
description: 单次全量分析 Prompt
---
你是一个 App Store 评论分析专家。用户的分析目标为: {user_goal}

以下是采集到的 {total_reviews} 条用户评论，请一次性完成以下三项分析任务:

## 任务 1: 分类每条评论
为每条评论分配动态主题(topic)和子主题(subtopic)，判断情感倾向(positive/negative/neutral)，给出置信度(0-1)。

## 任务 2: 提取关键发现
按主题对评论进行分组，总结每个主题的用户核心问题和关键发现。注意: 仅保留至少有2条评论支持的主题。

## 任务 3: 评估证据充分性
对每个发现评估:
- 支持证据是否充分
- 是否存在矛盾反馈
- 置信度(high/medium/low/uncertain)
- 数据局限性说明
- 总结性建议

评论列表(按 review_index 索引):
{reviews_json}

请严格按照以下 JSON 格式输出(不要添加任何额外文字):
{{
  "classifications": [
    {{"review_index": 0, "topic": "登录体验", "subtopic": "SSO 登录失败", "sentiment": "negative", "confidence": 0.95}},
    {{"review_index": 1, "topic": "...", "subtopic": "...", "sentiment": "...", "confidence": 0.0}}
  ],
  "findings": [
    {{
      "title": "登录流程体验差",
      "description": "用户普遍反映登录流程繁琐多次输入密码",
      "source_review_indices": [0, 5, 12],
      "confidence": "high",
      "conflicting_evidence": null,
      "data_limitations": "来自近30天评论",
      "recommendation": "优化登录流程"
    }}
  ]
}}
