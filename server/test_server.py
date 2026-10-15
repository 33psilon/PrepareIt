import os
import sys
import json
import asyncio
from unittest.mock import AsyncMock, MagicMock
from pathlib import Path

# Ensure server root is in sys.path
SERVER_ROOT = Path(__file__).resolve().parent
if str(SERVER_ROOT) not in sys.path:
    sys.path.insert(0, str(SERVER_ROOT))

from dotenv import load_dotenv
load_dotenv(SERVER_ROOT / ".env", override=True)

from pipecat.frames.frames import (
    LLMTextFrame,
    LLMFullResponseStartFrame,
    LLMFullResponseEndFrame,
    TranscriptionFrame,
    TextFrame,
)
from pipecat.processors.frame_processor import FrameDirection
from pipecat.processors.frameworks.rtvi import RTVIClientMessageFrame, RTVIServerMessageFrame
from pipecat.services.llm_service import FunctionCallParams

from state import InterviewState, InterviewPhase
from services.problem_service import ProblemService
from agents.editor_agent import validate_and_format_edit, MonacoRange, MonacoEditPayload
from agents.evaluator import _fallback_report, EvaluationReport, run_debrief_evaluator
from orchestrator import OrchestratorAgent, interview_tools
from bot import ResponseSeparatorProcessor, CodeAwareTranscriptProcessor


def test_api_keys():
    print("--- 1. Testing Environment & API Keys ---")
    deepgram_key = os.getenv("DEEPGRAM_API_KEY", "").strip()
    cartesia_key = os.getenv("CARTESIA_API_KEY", "").strip()
    google_key = os.getenv("GOOGLE_API_KEY", "").strip()
    print("  Deepgram Key Configured:", bool(deepgram_key))
    print("  Cartesia Key Configured:", bool(cartesia_key))
    print("  Google Key Configured:", bool(google_key))
    assert bool(google_key), "Google API key must be configured"
    assert bool(deepgram_key), "Deepgram API key must be configured"
    assert bool(cartesia_key), "Cartesia API key must be configured"
    print("  ✓ API keys check passed.")


def test_state_and_problem():
    print("--- 2. Testing ProblemService & InterviewState ---")
    prob_two_sum = ProblemService.fetch("two-sum")
    assert prob_two_sum.title == "Two Sum"
    assert prob_two_sum.difficulty == "Easy"
    assert len(prob_two_sum.constraints) > 0

    prob_pal = ProblemService.fetch("valid-palindrome")
    assert prob_pal.title == "Valid Palindrome"

    prob_cf = ProblemService.fetch("cf-123-A")
    assert "Codeforces" in prob_cf.title or "123" in prob_cf.id

    state = InterviewState(
        session_id="test-session-123",
        problem_title=prob_two_sum.title,
        problem_description=prob_two_sum.description,
    )
    assert state.current_phase == InterviewPhase.INTRO
    state.transition_to(InterviewPhase.CLARIFICATION)
    assert state.current_phase == InterviewPhase.CLARIFICATION
    state.transition_to(InterviewPhase.CODING)
    assert state.current_phase == InterviewPhase.CODING
    
    # Case-insensitive transition
    state.transition_to("hinting")
    assert state.current_phase == InterviewPhase.HINTING
    assert state.record_hint() == 1
    assert state.can_give_hint() is True
    assert state.record_hint() == 2
    assert state.record_hint() == 3
    assert state.can_give_hint() is False

    state.transition_to(InterviewPhase.CODING)
    assert state.current_phase == InterviewPhase.CODING
    state.transition_to(InterviewPhase.WRAPUP)
    assert state.current_phase == InterviewPhase.WRAPUP
    print("  ✓ ProblemService and InterviewState machine tests passed.")


def test_editor_agent():
    print("--- 3. Testing Safe Editor Agent & Monaco Validation ---")
    # Standard 1-based range edit
    edit_json_1 = json.dumps({
        "edits": [
            {
                "range": {"startLineNumber": 1, "startColumn": 1, "endLineNumber": 2, "endColumn": 10},
                "newText": "function twoSum(nums, target) {}"
            }
        ]
    })
    res1 = validate_and_format_edit(edit_json_1)
    assert res1 is not None
    assert len(res1["edits"]) == 1
    assert res1["edits"][0]["range"]["startLineNumber"] == 1

    # Simplified range {"start": 5, "end": 6}
    edit_json_2 = json.dumps({
        "edits": [
            {
                "range": {"start": 5, "end": 6},
                "newText": "// optimized loop"
            }
        ]
    })
    res2 = validate_and_format_edit(edit_json_2)
    assert res2 is not None
    assert res2["edits"][0]["range"]["startLineNumber"] == 5
    assert res2["edits"][0]["range"]["endLineNumber"] == 6

    # Markdown fenced json
    edit_json_3 = f"```json\n{edit_json_2}\n```"
    res3 = validate_and_format_edit(edit_json_3)
    assert res3 is not None
    assert res3["edits"][0]["newText"] == "// optimized loop"

    # Single edit without wrapping list
    edit_json_4 = json.dumps({
        "range": {"start": 2, "end": 3},
        "newText": "const map = new Map();"
    })
    res4 = validate_and_format_edit(edit_json_4)
    assert res4 is not None

    # Invalid input
    assert validate_and_format_edit("plain text error") is None
    assert validate_and_format_edit("") is None
    print("  ✓ EditorAgent validation tests passed.")


async def test_orchestrator_agent():
    print("--- 4. Testing OrchestratorAgent Policy & Tools ---")
    state = InterviewState(
        session_id="session-orch",
        problem_title="Two Sum",
        problem_description="Return indices summing to target",
    )
    orchestrator = OrchestratorAgent(state)

    # Test speech frame transcript collection
    speech_frame = TranscriptionFrame(text="Hello, I am ready to start.", user_id="cand_1", timestamp=100)
    pushed = []
    orchestrator.push_frame = AsyncMock(side_effect=lambda f, d: pushed.append(f))
    await orchestrator.process_frame(speech_frame, FrameDirection.DOWNSTREAM)
    assert len(orchestrator.transcript) == 1
    assert "Hello, I am ready to start." in orchestrator.transcript[0]

    # Test code update sync
    code_frame = TextFrame(text="CODE_UPDATE:function solution() {}")
    await orchestrator.process_frame(code_frame, FrameDirection.DOWNSTREAM)
    assert state.latest_code == "function solution() {}"

    # Test advance_interview_phase tool
    callback_result = None
    async def mock_callback(res):
        nonlocal callback_result
        callback_result = res

    params = FunctionCallParams(
        function_name="advance_interview_phase",
        tool_call_id="call_1",
        arguments={"target_phase": "CLARIFICATION"},
        llm=MagicMock(),
        context=MagicMock(),
        result_callback=mock_callback,
    )
    await orchestrator.advance_interview_phase(params)
    assert callback_result["ok"] is True
    assert callback_result["current_phase"] == "CLARIFICATION"

    # Test request_code_review tool
    params_review = FunctionCallParams(
        function_name="request_code_review",
        tool_call_id="call_2",
        arguments={},
        llm=MagicMock(),
        context=MagicMock(),
        result_callback=mock_callback,
    )
    await orchestrator.request_code_review(params_review)
    assert callback_result["ok"] is True
    assert callback_result["latest_code"] == "function solution() {}"

    # Test record_hint_given tool
    params_hint = FunctionCallParams(
        function_name="record_hint_given",
        tool_call_id="call_3",
        arguments={"topic": "Use Hash Map"},
        llm=MagicMock(),
        context=MagicMock(),
        result_callback=mock_callback,
    )
    await orchestrator.record_hint_given(params_hint)
    assert callback_result["ok"] is True
    assert callback_result["hints_used"] == 1
    print("  ✓ OrchestratorAgent transcript & tools tests passed.")


async def test_response_separator_processor():
    print("--- 5. Testing ResponseSeparatorProcessor ---")
    mock_rtvi = MagicMock()
    rtvi_messages = []
    mock_rtvi.push_frame = AsyncMock(side_effect=lambda f: rtvi_messages.append(f))

    separator = ResponseSeparatorProcessor(mock_rtvi)
    downstream_frames = []
    separator.push_frame = AsyncMock(side_effect=lambda f, d: downstream_frames.append(f))

    # Start of response turn
    await separator.process_frame(LLMFullResponseStartFrame(), FrameDirection.DOWNSTREAM)
    assert separator.state == "notDecided"

    # Audio chunk
    await separator.process_frame(LLMTextFrame(text="🔊 Great job explaining your approach."), FrameDirection.DOWNSTREAM)
    assert separator.state == "audio"
    assert any(isinstance(f, LLMTextFrame) and "Great job" in f.text for f in downstream_frames)

    # Code chunk
    await separator.process_frame(LLMTextFrame(text='💻 {"edits": [{"range": {"start": 1, "end": 1}, "newText": "// start"}]}'), FrameDirection.DOWNSTREAM)
    assert separator.state == "code"
    assert any(isinstance(f, RTVIServerMessageFrame) and f.data["type"] == "code_response_chunk" for f in rtvi_messages)

    # End of response turn
    await separator.process_frame(LLMFullResponseEndFrame(), FrameDirection.DOWNSTREAM)
    assert separator.state == "notDecided"
    assert any(isinstance(f, RTVIServerMessageFrame) and f.data["type"] == "code_response_complete" for f in rtvi_messages)
    print("  ✓ ResponseSeparatorProcessor routing & reset tests passed.")


async def test_code_aware_transcript_processor():
    print("--- 6. Testing CodeAwareTranscriptProcessor ---")
    proc = CodeAwareTranscriptProcessor()
    downstream = []
    proc.push_frame = AsyncMock(side_effect=lambda f, d: downstream.append(f))

    # Send code message from client
    client_msg = RTVIClientMessageFrame(msg_id="msg_123", type="send_code", data={"code": "const x = 10;", "timestamp": 12345})
    await proc.process_frame(client_msg, FrameDirection.DOWNSTREAM)
    assert proc._current_code == "const x = 10;"

    # Voice transcription after code update
    voice_frame = TranscriptionFrame(text="I defined x as 10", user_id="user_1", timestamp=100)
    await proc.process_frame(voice_frame, FrameDirection.DOWNSTREAM)
    enhanced = downstream[-1]
    assert isinstance(enhanced, TranscriptionFrame)
    assert "Voice: I defined x as 10" in enhanced.text
    assert "Code:\n```\nconst x = 10;\n```" in enhanced.text
    print("  ✓ CodeAwareTranscriptProcessor code enhancement tests passed.")


async def test_evaluator_agent():
    print("--- 7. Testing Live Evaluator Agent with Gemini 3.6 Flash ---")
    fallback = _fallback_report()
    assert fallback.verdict == "Incomplete"

    api_key = os.getenv("GOOGLE_API_KEY", "").strip()
    if api_key:
        transcript = (
            "Interviewer: Welcome to your mock DSA interview. Today we will solve Two Sum.\n"
            "Candidate: Sounds great! I'll clarify the problem.\n"
            "Candidate: I will use a hash map to achieve O(n) time complexity and O(n) space.\n"
            "Interviewer: That's a great approach, go ahead and code it.\n"
            "Candidate: Done! I have tested with example [2,7,11,15] target 9."
        )
        final_code = (
            "function twoSum(nums, target) {\n"
            "    const map = new Map();\n"
            "    for (let i = 0; i < nums.length; i++) {\n"
            "        const comp = target - nums[i];\n"
            "        if (map.has(comp)) return [map.get(comp), i];\n"
            "        map.set(nums[i], i);\n"
            "    }\n"
            "    return [];\n"
            "}"
        )
        report = await run_debrief_evaluator(
            transcript=transcript,
            final_code=final_code,
            problem_desc="Given an array of integers nums and an integer target, return indices of the two numbers that add up to target.",
        )
        print(f"  Live Evaluator Verdict: {report.verdict}")
        print(f"  Scores: Problem Solving={report.problem_solving_score}/10, Code Quality={report.code_quality_score}/10, Communication={report.communication_score}/10")
        print(f"  Complexity: Time={report.time_complexity}, Space={report.space_complexity}")
        print(f"  Strengths: {report.key_strengths}")
        assert report.problem_solving_score >= 7
        assert report.code_quality_score >= 7
    print("  ✓ EvaluatorAgent live evaluation tests passed.")


async def main():
    print("\n=======================================================")
    print("RUNNING COMPREHENSIVE SERVER & AGENT TEST SUITE")
    print("=======================================================")
    test_api_keys()
    test_state_and_problem()
    test_editor_agent()
    await test_orchestrator_agent()
    await test_response_separator_processor()
    await test_code_aware_transcript_processor()
    await test_evaluator_agent()
    print("\n=======================================================")
    print("ALL 7 TEST SUITES PASSED SUCCESSFULLY!")
    print("=======================================================\n")

if __name__ == "__main__":
    asyncio.run(main())
