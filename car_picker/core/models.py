from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from random import Random
from typing import Dict, List, Optional


class QuizMode(str, Enum):
    """Available quiz modes."""

    MAKE = "make"
    MAKE_MODEL = "make_model"
    MAKE_MODEL_YEAR = "make_model_year"

    @property
    def display_name(self) -> str:
        mapping = {
            QuizMode.MAKE: "Make Only",
            QuizMode.MAKE_MODEL: "Make + Model",
            QuizMode.MAKE_MODEL_YEAR: "Make + Model + Year",
        }
        return mapping[self]


@dataclass(frozen=True)
class CarImage:
    """Metadata for a single car image."""

    id: str
    path: Path
    make: str
    model: str
    year: int
    random_id: str
    specs: Dict[str, str]


@dataclass(frozen=True)
class AnswerChoice:
    """Represents an answer option for a quiz question."""

    id: str
    label: str
    car: CarImage


@dataclass(frozen=True)
class QuizQuestion:
    """A question consisting of the prompt image and answer choices."""

    number: int
    car: CarImage
    choices: List[AnswerChoice]


@dataclass(frozen=True)
class ScoreDetail:
    """Granular scoring outcome for a question."""

    points: float
    max_points: float
    make_correct: bool
    model_correct: bool
    year_correct: bool
    mode: QuizMode


@dataclass(frozen=True)
class QuestionResult:
    """Stores the outcome of a completed question."""

    question: QuizQuestion
    selected_choice: AnswerChoice
    score: ScoreDetail


@dataclass
class QuizState:
    """Mutable session state for the quiz."""

    mode: QuizMode
    total_questions: int = 10
    duration_seconds: int = 600
    used_ids: set[str] = field(default_factory=set)
    history: List[QuestionResult] = field(default_factory=list)
    current_question: Optional[QuizQuestion] = None
    score: float = 0.0
    start_time: Optional[float] = None
    completed: bool = False
    rng_seed: Optional[int] = None
    rng: Optional[Random] = field(default=None, repr=False)
