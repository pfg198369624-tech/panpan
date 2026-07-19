import time
import json
import logging
from typing import Optional
import httpx
from app.core.config import settings

logger = logging.getLogger(__name__)


class AICallResult:
    def __init__(self, success: bool, text: str = "", error: str = "", tokens: int = 0,
                 prompt_tokens: int = 0, completion_tokens: int = 0, duration_ms: int = 0,
                 retry_count: int = 0):
        self.success = success
        self.text = text
        self.error = error
        self.tokens = tokens
        self.prompt_tokens = prompt_tokens
        self.completion_tokens = completion_tokens
        self.duration_ms = duration_ms
        self.retry_count = retry_count


class AIClient:
    def __init__(self):
        self.api_url = settings.volc_api_url
        self.model_name = settings.volc_model_name
        self.api_key = settings.volc_api_key
        self.timeout = settings.ai_timeout
        self.max_retries = settings.ai_max_retries
        self.temperature = settings.ai_temperature
        self.max_tokens = settings.ai_max_tokens

    async def _call_once(self, prompt: str) -> tuple[str, int, int]:
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }
        payload = {
            "model": self.model_name,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
        }
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.post(self.api_url, headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()
            choice = data["choices"][0]
            content = choice["message"].get("content") or ""
            usage = data.get("usage", {})
            prompt_tokens = usage.get("prompt_tokens", 0)
            completion_tokens = usage.get("completion_tokens", 0)
            return content, prompt_tokens, completion_tokens

    async def call(self, prompt: str, task: str = "") -> AICallResult:
        last_error = ""
        for attempt in range(self.max_retries):
            start = time.time()
            try:
                text, prompt_tokens, completion_tokens = await self._call_once(prompt)
                duration = int((time.time() - start) * 1000)
                return AICallResult(
                    success=True,
                    text=text,
                    tokens=prompt_tokens + completion_tokens,
                    prompt_tokens=prompt_tokens,
                    completion_tokens=completion_tokens,
                    duration_ms=duration,
                    retry_count=attempt,
                )
            except Exception as e:
                last_error = str(e)
                logger.warning(f"AI call failed (attempt {attempt + 1}/{self.max_retries}): {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(settings.ai_backoff_base ** attempt)
        return AICallResult(
            success=False,
            error=f"AI call failed after {self.max_retries} retries: {last_error}",
            retry_count=self.max_retries,
        )


ai_client = AIClient()
