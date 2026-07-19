---
model: doubao
temperature: 0.3
max_tokens: 2048
version: v1
description: 深度分析 Prompt
---
以下是一组关于 "{topic}" 主题的用户评论 ({count}条)。
请分析用户核心问题是什么，并总结出关键发现。

评论:
{reviews_text}

输出 JSON:
{{
  "core_problem": "用户核心问题描述",
  "key_findings": ["发现1", "发现2"],
  "severity": "high/medium/low"
}}
