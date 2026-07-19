from typing import Optional, Union, List
from pydantic import BaseModel
import json
import re
import logging

logger = logging.getLogger(__name__)


class AIOutputValidator:
    @staticmethod
    def repair_json(raw: str) -> str:
        if raw is None:
            return ""
        text = raw.strip()
        if text.startswith("```"):
            lines = text.split("\n")
            lines = [l for l in lines if not l.startswith("```")]
            text = "\n".join(lines).strip()

        text = re.sub(r",\s*([}\]])", r"\1", text)
        return text

    @staticmethod
    def parse_and_validate(raw: str, schema_model: type[BaseModel]) -> Optional[Union[BaseModel, List[BaseModel]]]:
        if raw is None:
            logger.error(f"Validation failed for {schema_model.__name__}: raw input is None")
            return None
        try:
            repaired = AIOutputValidator.repair_json(raw)

            try:
                data = json.loads(repaired)
            except json.JSONDecodeError:
                data = json.loads(repaired.replace("'", '"'))

            if isinstance(data, list):
                result = []
                for item in data:
                    result.append(schema_model.model_validate(item))
                return result
            return schema_model.model_validate(data)
        except Exception as e:
            logger.error(f"Validation failed for {schema_model.__name__}: {e}")
            logger.error(f"Raw AI response (first 500 chars): {str(raw)[:500]}")
            return None
