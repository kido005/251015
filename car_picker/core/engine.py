from __future__ import annotations

import random
import time
from typing import Optional

from .indexer import DatasetIndex
from .models import (
    AnswerChoice,
    CarImage,
    QuestionResult,
    QuizMode,
    QuizQuestion,
    QuizState,
    ScoreDetail,
)
from .options import generate_choices

DEFAULT_TOTAL_QUESTIONS = 10
DEFAULT_DURATION_SECONDS = 10 * 60  # 10 minutes
DEFAULT_CHOICE_COUNT = 10


def create_quiz_state(
    mode: QuizMode,
    total_questions: int = DEFAULT_TOTAL_QUESTIONS,
    duration_seconds: int = DEFAULT_DURATION_SECONDS,
    seed: Optional[int] = None,
) -> QuizState:
    state = QuizState(
        mode=mode,
        total_questions=total_questions,
        duration_seconds=duration_seconds,
    )
    reset_quiz_state(state, mode=mode, duration_seconds=duration_seconds, seed=seed)
    return state


def reset_quiz_state(
    state: QuizState,
    mode: QuizMode,
    duration_seconds: int = DEFAULT_DURATION_SECONDS,
    seed: Optional[int] = None,
) -> None:
    state.mode = mode
    state.duration_seconds = duration_seconds
    state.used_ids.clear()
    state.history.clear()
    state.current_question = None
    state.score = 0.0
    state.completed = False
    state.start_time = time.time()
    if seed is None:
        seed = time.time_ns()
    state.rng_seed = seed
    state.rng = random.Random(seed)


def ensure_question(state: QuizState, index: DatasetIndex) -> Optional[QuizQuestion]:
    if state.completed:
        return None

    if is_time_up(state):
        state.completed = True
        return None

    if state.current_question is not None:
        return state.current_question

    if len(state.history) >= state.total_questions:
        state.completed = True
        return None

    rng = state.rng or random.Random(state.rng_seed)
    state.rng = rng

    car = _select_car(index, state, rng)
    choices = generate_choices(car, index, state.mode, total_choices=DEFAULT_CHOICE_COUNT, rng=rng)
    question_number = len(state.history) + 1
    question = QuizQuestion(number=question_number, car=car, choices=choices)
    state.current_question = question
    state.used_ids.add(car.id)
    return question


def submit_answer(state: QuizState, choice_id: str) -> ScoreDetail:
    if state.current_question is None:
        raise RuntimeError("No active question to submit.")

    selected = _find_choice(state.current_question, choice_id)
    if selected is None:
        raise ValueError("Selected choice not found in current question.")

    correct_car = state.current_question.car
    score_detail = _compute_score(correct_car, selected.car, state.mode)

    state.score += score_detail.points
    result = QuestionResult(question=state.current_question, selected_choice=selected, score=score_detail)
    state.history.append(result)
    state.current_question = None

    if len(state.history) >= state.total_questions or is_time_up(state):
        state.completed = True

    return score_detail


def remaining_questions(state: QuizState) -> int:
    return max(0, state.total_questions - len(state.history))


def is_time_up(state: QuizState) -> bool:
    if state.start_time is None:
        return False
    return (time.time() - state.start_time) >= state.duration_seconds


def remaining_seconds(state: QuizState) -> float:
    if state.start_time is None:
        return state.duration_seconds
    elapsed = time.time() - state.start_time
    return max(0.0, state.duration_seconds - elapsed)


def _select_car(index: DatasetIndex, state: QuizState, rng: random.Random) -> CarImage:
    pool = index.get_random_pool()
    if not pool:
        raise RuntimeError("Dataset index is empty.")

    available = len(pool) - len(state.used_ids)
    if available <= 0:
        # Reset used ids but keep history to avoid crash; future enhancement could allow repeats.
        state.used_ids.clear()

    for _ in range(256):
        candidate = rng.choice(pool)
        if candidate.id not in state.used_ids:
            return candidate

    for candidate in pool:
        if candidate.id not in state.used_ids:
            return candidate

    raise RuntimeError("Unable to select a new car for the question.")


def _find_choice(question: QuizQuestion, choice_id: str) -> Optional[AnswerChoice]:
    for choice in question.choices:
        if choice.id == choice_id:
            return choice
    return None


def _compute_score(correct: CarImage, guess: CarImage, mode: QuizMode) -> ScoreDetail:
    make_correct = guess.make == correct.make
    model_correct = make_correct and (guess.model == correct.model)
    year_correct = model_correct and (guess.year == correct.year)

    if mode == QuizMode.MAKE:
        points = 1.0 if make_correct else 0.0
    elif mode == QuizMode.MAKE_MODEL:
        points = 0.0
        if make_correct:
            points += 0.5
            if model_correct:
                points += 0.5
    else:  # QuizMode.MAKE_MODEL_YEAR
        points = 0.0
        if make_correct:
            points += 0.3
            if model_correct:
                points += 0.4
                if year_correct:
                    points += 0.3

    return ScoreDetail(
        points=points,
        max_points=1.0,
        make_correct=make_correct,
        model_correct=model_correct,
        year_correct=year_correct,
        mode=mode,
    )
