from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class InterviewPhase(str, Enum):
    INTRO = "INTRO"
    CLARIFICATION = "CLARIFICATION"
    CODING = "CODING"
    HINTING = "HINTING"
    WRAPUP = "WRAPUP"

    @classmethod
    def from_str(cls, value: str) -> "InterviewPhase":
        normalized = value.strip().upper()
        for member in cls:
            if member.value == normalized:
                return member
        raise ValueError(f"Unknown interview phase: {value}")


class InterviewState(BaseModel):
    session_id: str
    problem_title: str
    problem_description: str
    current_phase: InterviewPhase = InterviewPhase.INTRO
    hints_given: int = Field(default=0, ge=0)
    max_hints: int = Field(default=3, ge=1)
    latest_code: str = ""

    _allowed_transitions = {
        InterviewPhase.INTRO: {InterviewPhase.CLARIFICATION, InterviewPhase.CODING},
        InterviewPhase.CLARIFICATION: {InterviewPhase.CODING, InterviewPhase.HINTING, InterviewPhase.WRAPUP},
        InterviewPhase.CODING: {InterviewPhase.HINTING, InterviewPhase.WRAPUP, InterviewPhase.CLARIFICATION},
        InterviewPhase.HINTING: {InterviewPhase.CODING, InterviewPhase.WRAPUP},
        InterviewPhase.WRAPUP: set(),
    }

    def transition_to(self, new_phase: str | InterviewPhase) -> "InterviewState":
        if isinstance(new_phase, str):
            phase_enum = InterviewPhase.from_str(new_phase)
        else:
            phase_enum = new_phase

        if phase_enum == self.current_phase:
            return self

        if phase_enum not in self._allowed_transitions.get(self.current_phase, set()):
            raise ValueError(f"Invalid phase transition: {self.current_phase.value} -> {phase_enum.value}")
        self.current_phase = phase_enum
        return self

    def record_hint(self) -> int:
        self.hints_given += 1
        return self.hints_given

    def can_give_hint(self) -> bool:
        return self.hints_given < self.max_hints

