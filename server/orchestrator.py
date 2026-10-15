from loguru import logger
from pipecat.frames.frames import (
    Frame,
    LLMMessagesFrame,
    LLMTextFrame,
    TextFrame,
    TranscriptionFrame,
    InterimTranscriptionFrame,
)
from pipecat.processors.frame_processor import FrameDirection, FrameProcessor
from pipecat.services.llm_service import FunctionCallParams

try:
    from .state import InterviewPhase, InterviewState
except ImportError:
    from state import InterviewPhase, InterviewState


class OrchestratorAgent(FrameProcessor):
    """Deterministic interview policy and transcript coordinator for the LLM pipeline."""

    def __init__(self, state: InterviewState, **kwargs):
        super().__init__(**kwargs)
        self.state = state
        self.transcript: list[str] = []
        self._current_assistant_turn: list[str] = []

    def system_prompt(self) -> str:
        phase_guidance = {
            InterviewPhase.INTRO: (
                "Warmly introduce yourself as the technical interviewer. State that you will be assessing "
                "problem-solving, communication, and DSA implementation skills. Ask if they are ready to begin."
            ),
            InterviewPhase.CLARIFICATION: (
                "Present the problem clearly. In 💻 present the problem name, examples, and constraints. In 🔊 ask the candidate "
                "to explain their understanding, explore edge cases, and describe their proposed approach with time/space complexities "
                "before writing code. Transition to CODING once approach is solid."
            ),
            InterviewPhase.CODING: (
                "Candidate is now implementing their solution in the editor. Observe their code updates and explain what you're seeing. "
                "If they are stuck or ask for help, switch to HINTING. If they finish and test their code, verify complexity and move to WRAPUP."
            ),
            InterviewPhase.HINTING: (
                f"Provide a targeted, progressive hint (Hint {self.state.hints_given + 1}/{self.state.max_hints}). "
                "Do not give away the entire solution immediately; nudge them toward the right invariant or data structure."
            ),
            InterviewPhase.WRAPUP: (
                "Conclude the interview. Ask the candidate to summarize their final time/space complexity. "
                "Give polite closing remarks and let them know the evaluation is being prepared."
            ),
        }

        current_phase_desc = phase_guidance.get(self.state.current_phase, "Conduct the interview professionally.")

        return (
            f"=== CURRENT INTERVIEW STATE ===\n"
            f"Phase: {self.state.current_phase.value}\n"
            f"Problem: {self.state.problem_title}\n"
            f"Description & Constraints: {self.state.problem_description}\n"
            f"Hints Used: {self.state.hints_given}/{self.state.max_hints}\n"
            f"Phase Objective: {current_phase_desc}\n"
            f"===============================\n"
            "Rules:\n"
            "1. Always output 🔊 for spoken speech (audio).\n"
            "2. Whenever sharing problem statements, code examples, or edits, put them in 💻.\n"
            "3. When editing code, output clean JSON with { \"edits\": [ { \"range\": { \"start\": line, \"end\": line }, \"newText\": \"code\" } ] }.\n"
            "4. Call advance_interview_phase when moving between interview milestones.\n"
        )

    async def process_frame(self, frame: Frame, direction: FrameDirection):
        # Intercept code synchronization updates
        if isinstance(frame, TextFrame) and frame.text.startswith("CODE_UPDATE:"):
            self.state.latest_code = frame.text.removeprefix("CODE_UPDATE:").strip()
            await self.push_frame(frame, direction)
            return

        # Intercept candidate speech transcription frames
        if isinstance(frame, TranscriptionFrame) and not isinstance(frame, InterimTranscriptionFrame):
            speech_text = frame.text.strip()
            if speech_text:
                self.transcript.append(f"Candidate: {speech_text}")
                logger.info(f"[Transcript] Candidate: {speech_text}")

        # Intercept assistant responses to record in transcript
        if isinstance(frame, LLMTextFrame):
            if frame.text:
                self._current_assistant_turn.append(frame.text)

        # Intercept explicit message frames to inject state prompt
        if isinstance(frame, LLMMessagesFrame):
            frame.messages.insert(0, {"role": "system", "content": self.system_prompt()})

        await self.push_frame(frame, direction)

    async def advance_interview_phase(self, params: FunctionCallParams):
        target = params.arguments.get("target_phase", "")
        logger.info(f"LLM requesting phase transition to: '{target}' from current: '{self.state.current_phase.value}'")
        try:
            self.state.transition_to(target)
            result = {
                "ok": True,
                "current_phase": self.state.current_phase.value,
                "hints_used": f"{self.state.hints_given}/{self.state.max_hints}",
                "guidance": f"Phase successfully transitioned to {self.state.current_phase.value}. Continue interview.",
            }
        except Exception as e:
            logger.warning(f"Failed phase transition: {e}")
            result = {
                "ok": False,
                "current_phase": self.state.current_phase.value,
                "error": str(e),
            }
        await params.result_callback(result)

    async def request_code_review(self, params: FunctionCallParams):
        logger.info(f"LLM requested code review during phase: {self.state.current_phase.value}")
        code_snapshot = self.state.latest_code or "(Editor is currently empty)"
        result = {
            "ok": True,
            "phase": self.state.current_phase.value,
            "latest_code": code_snapshot,
            "hints_given": self.state.hints_given,
            "max_hints": self.state.max_hints,
        }
        await params.result_callback(result)

    async def record_hint_given(self, params: FunctionCallParams):
        hint_topic = params.arguments.get("topic", "General hint")
        hints_used = self.state.record_hint()
        logger.info(f"Hint recorded ({hints_used}/{self.state.max_hints}): {hint_topic}")
        result = {
            "ok": True,
            "hints_used": hints_used,
            "max_hints": self.state.max_hints,
            "can_give_more": self.state.can_give_hint(),
        }
        await params.result_callback(result)


def interview_tools() -> list[dict]:
    return [
        {
            "function_declarations": [
                {
                    "name": "advance_interview_phase",
                    "description": "Advance the interview to the next valid phase (INTRO -> CLARIFICATION -> CODING <-> HINTING -> WRAPUP).",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "target_phase": {
                                "type": "string",
                                "enum": [phase.value for phase in InterviewPhase],
                                "description": "The target interview phase to transition into.",
                            }
                        },
                        "required": ["target_phase"],
                    },
                },
                {
                    "name": "request_code_review",
                    "description": "Inspect the candidate's current editor code snapshot and check current progress.",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                    },
                },
                {
                    "name": "record_hint_given",
                    "description": "Record that a hint has been given to the candidate to track hint quota.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "topic": {
                                "type": "string",
                                "description": "Brief summary of the hint provided.",
                            }
                        },
                    },
                },
            ]
        }
    ]
