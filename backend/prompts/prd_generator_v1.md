---
model: doubao
temperature: 0.4
max_tokens: 4096
version: v1
description: PRD 生成 Prompt
---
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
{{
  "versions": [
    {{
      "version": "v1.0",
      "name": "MVP",
      "requirements": [
        {{
          "req_id": "REQ-001",
          "title": "...",
          "description": "...",
          "priority": "P0",
          "source_finding_ids": [1, 2],
          "source_review_excerpts": ["..."]
        }}
      ]
    }}
  ]
}}
