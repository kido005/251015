from __future__ import annotations

import time

from .models import QuizState


def ensure_started(state: QuizState) -> float:
    if state.start_time is None:
        state.start_time = time.time()
    return state.start_time


def remaining_seconds(state: QuizState) -> float:
    ensure_started(state)
    elapsed = time.time() - (state.start_time or time.time())
    return max(0.0, state.duration_seconds - elapsed)


def expired(state: QuizState) -> bool:
    return remaining_seconds(state) <= 0.0
