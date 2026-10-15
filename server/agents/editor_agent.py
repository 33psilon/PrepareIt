import json
import re
from typing import Any
from loguru import logger
from pydantic import BaseModel, Field, ValidationError, field_validator


class MonacoRange(BaseModel):
    startLineNumber: int = Field(ge=1)
    startColumn: int = Field(default=1, ge=1)
    endLineNumber: int = Field(ge=1)
    endColumn: int = Field(default=1, ge=1)

    @field_validator("endLineNumber")
    @classmethod
    def end_line_not_before_start(cls, value: int, info: Any) -> int:
        start = info.data.get("startLineNumber")
        if start is not None and value < start:
            raise ValueError("endLineNumber must be >= startLineNumber")
        return value


class MonacoEditPayload(BaseModel):
    edits: list[dict]

    @field_validator("edits")
    @classmethod
    def valid_edits(cls, value: list[dict]) -> list[dict]:
        normalized = []
        for edit in value:
            if not isinstance(edit, dict) or not isinstance(edit.get("newText"), str):
                raise ValueError("Each edit requires string newText")
            raw_range = edit.get("range")
            if isinstance(raw_range, dict) and {"startLineNumber", "endLineNumber"}.issubset(raw_range):
                edit_range = MonacoRange.model_validate(raw_range)
            elif isinstance(raw_range, dict) and {"start", "end"}.issubset(raw_range):
                edit_range = MonacoRange(
                    startLineNumber=int(raw_range["start"]),
                    startColumn=int(raw_range.get("startColumn", 1)),
                    endLineNumber=int(raw_range["end"]),
                    endColumn=int(raw_range.get("endColumn", 1)),
                )
            else:
                # Default to inserting at line 1 if range unspecified
                edit_range = MonacoRange(startLineNumber=1, startColumn=1, endLineNumber=1, endColumn=1)

            normalized.append({"range": edit_range.model_dump(), "newText": edit["newText"]})
        return normalized


def validate_and_format_edit(raw_json: str) -> dict | None:
    if not raw_json or not raw_json.strip():
        return None

    cleaned = raw_json.strip()
    # Strip markdown fences if present
    fence_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", cleaned, re.DOTALL)
    if fence_match:
        cleaned = fence_match.group(1)
    else:
        brace_match = re.search(r"(\{.*\})", cleaned, re.DOTALL)
        if brace_match:
            cleaned = brace_match.group(1)

    try:
        data = json.loads(cleaned)
        if isinstance(data, dict) and "edits" in data:
            payload = MonacoEditPayload.model_validate(data)
            return payload.model_dump()
        if isinstance(data, dict) and ("range" in data or "newText" in data):
            payload = MonacoEditPayload.model_validate({"edits": [data]})
            return payload.model_dump()
        return None
    except (json.JSONDecodeError, TypeError, ValidationError, ValueError) as e:
        logger.debug(f"Editor payload validation failed for: {raw_json[:100]}... Error: {e}")
        return None

