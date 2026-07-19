---
model: doubao
temperature: 0.3
max_tokens: 2048
version: v1
description: 追溯验证 Prompt
---
检查以下需求是否确实来源于用户反馈，验证追溯链完整性:

需求: {req_title}
描述: {req_description}
关联发现: {findings_text}
关联评论: {reviews_text}

要求:
1. 判断该需求是否合理地从用户评论推导而来
2. 如果需求没有足够的用户反馈支撑，给出修改建议

输出 JSON:
{{
  "is_grounded_in_reviews": true/false,
  "reasoning": "推理过程",
  "suggestion": "如果无支撑请给出建议"
}}
