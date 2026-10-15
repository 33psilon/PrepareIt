import asyncio
import json
import os
import re
from loguru import logger
from pydantic import BaseModel, Field


class EvaluationReport(BaseModel):
    verdict: str
    problem_solving_score: int = Field(ge=0, le=10)
    code_quality_score: int = Field(ge=0, le=10)
    communication_score: int = Field(ge=0, le=10)
    time_complexity: str
    space_complexity: str
    key_strengths: list[str]
    areas_for_improvement: list[str]


def _fallback_report() -> EvaluationReport:
    return EvaluationReport(
        verdict="Incomplete",
        problem_solving_score=0,
        code_quality_score=0,
        communication_score=0,
        time_complexity="Not established",
        space_complexity="Not established",
        key_strengths=[],
        areas_for_improvement=["Complete a full interview session for a meaningful evaluation."],
    )


def _extract_json_payload(text: str) -> dict:
    # Attempt direct load
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Attempt to extract JSON from markdown code fences or curly braces
    fence_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if fence_match:
        return json.loads(fence_match.group(1))

    brace_match = re.search(r"(\{.*\})", text, re.DOTALL)
    if brace_match:
        return json.loads(brace_match.group(1))

    raise ValueError("No valid JSON payload found in model output")


async def run_debrief_evaluator(transcript: str, final_code: str, problem_desc: str) -> EvaluationReport:
    prompt = (
        "You are an expert technical interviewer evaluating a completed DSA coding interview session.\n"
        f"Problem Description: {problem_desc}\n"
        f"Interview Transcript:\n{transcript or '(No transcript recorded)'}\n"
        f"Candidate Final Code:\n{final_code or '(No code written)'}\n\n"
        "Evaluate the session rigorously. Return only a JSON object matching this schema:\n"
        "{\n"
        '  "verdict": "Hire" | "No Hire" | "Strong Hire" | "Incomplete",\n'
        '  "problem_solving_score": <0-10 integer>,\n'
        '  "code_quality_score": <0-10 integer>,\n'
        '  "communication_score": <0-10 integer>,\n'
        '  "time_complexity": "<e.g. O(n) or Not established>",\n'
        '  "space_complexity": "<e.g. O(1) or Not established>",\n'
        '  "key_strengths": ["string", ...],\n'
        '  "areas_for_improvement": ["string", ...]\n'
        "}"
    )

    def generate() -> EvaluationReport:
        try:
            from google import genai
            api_key = os.getenv("GOOGLE_API_KEY", "").strip()
            if not api_key:
                logger.warning("GOOGLE_API_KEY not configured for debrief evaluation")
                return _fallback_report()

            client = genai.Client(api_key=api_key)
            response = client.models.generate_content(
                model="gemini-3.6-flash",
                contents=prompt,
                config={"response_mime_type": "application/json"},
            )
            raw_text = response.text or ""
            data = _extract_json_payload(raw_text)
            report = EvaluationReport.model_validate(data)
            logger.info(f"Debrief evaluation complete: Verdict={report.verdict}, Scores=({report.problem_solving_score}, {report.code_quality_score}, {report.communication_score})")
            return report
        except Exception as e:
            logger.error(f"Error generating debrief evaluation: {e}")
            return _fallback_report()

    return await asyncio.to_thread(generate)

