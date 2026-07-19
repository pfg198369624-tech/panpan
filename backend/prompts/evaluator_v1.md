---
model: doubao
temperature: 0.3
max_tokens: 2048
version: v1
description: 证据评估 Prompt
---
检查以下发现中是否存在矛盾的用户反馈，评估证据充分性:

主题: {topic}
支持评论: {supporting_reviews}
反对评论: {opposing_reviews}

输出 JSON:
{{
  "evidence_sufficient": true/false,
  "conflicting_feedback": "矛盾描述或 null",
  "confidence": "high/medium/low/uncertain",
  "data_limitations": "数据局限性说明",
  "recommendation": "建议"
}}
