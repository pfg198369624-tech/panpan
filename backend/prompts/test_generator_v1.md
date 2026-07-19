---
model: doubao
temperature: 0.4
max_tokens: 4096
version: v1
description: 测试用例生成 Prompt
---
基于以下产品需求生成测试用例:

需求: {req_title}
描述: {req_description}
关联用户评论: {source_reviews}

要求:
1. 测试用例必须能验证该需求是否解决了用户评论中提出的问题
2. 包含前置条件、测试步骤、预期结果
3. 关联到原始评论 ID

输出 JSON:
{{
  "test_cases": [
    {{
      "case_id": "TC-001",
      "title": "...",
      "preconditions": "...",
      "steps": ["步骤1", "步骤2"],
      "expected_result": "...",
      "source_review_ids": [1, 2, 3]
    }}
  ]
}}
