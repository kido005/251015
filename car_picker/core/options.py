from __future__ import annotations

import random
from typing import List, Sequence, Set

from .indexer import DatasetIndex
from .models import AnswerChoice, CarImage, QuizMode


def format_label(car: CarImage, mode: QuizMode) -> str:
    if mode == QuizMode.MAKE:
        return car.make
    if mode == QuizMode.MAKE_MODEL:
        return f"{car.make} {car.model}"
    return f"{car.make} {car.model} {car.year}"


def generate_choices(
    correct: CarImage,
    index: DatasetIndex,
    mode: QuizMode,
    total_choices: int = 10,
    rng: random.Random | None = None,
) -> List[AnswerChoice]:
    """Create a list of answer choices including the correct answer."""
    if total_choices < 2:
        raise ValueError("total_choices must be at least 2.")

    rng = rng or random.Random()
    seen_ids: Set[str] = {correct.id}
    seen_labels: Set[str] = {format_label(correct, mode)}

    distractors: List[CarImage] = []

    pools: List[Sequence[CarImage]] = []

    if mode == QuizMode.MAKE_MODEL_YEAR:
        same_model = [
            car
            for car in index.get_by_make_model(correct.make, correct.model)
            if car.id not in seen_ids and car.year != correct.year
        ]
        same_make = [
            car
            for car in index.get_by_make(correct.make)
            if car.id not in seen_ids and (car.model != correct.model or car.year != correct.year)
        ]
        pools.extend([same_model, same_make])
    elif mode == QuizMode.MAKE_MODEL:
        same_model = [
            car
            for car in index.get_by_make_model(correct.make, correct.model)
            if car.id not in seen_ids and car.year != correct.year
        ]
        same_make = [
            car
            for car in index.get_by_make(correct.make)
            if car.id not in seen_ids and car.model != correct.model
        ]
        pools.extend([same_model, same_make])
    elif mode == QuizMode.MAKE:
        other_makes = [
            car for car in index.get_random_pool() if car.id not in seen_ids and car.make != correct.make
        ]
        pools.append(other_makes)

    all_pool = [car for car in index.get_random_pool() if car.id not in seen_ids]
    pools.append(all_pool)

    for pool in pools:
        pool_list = list(pool)
        rng.shuffle(pool_list)
        for car in pool_list:
            if len(distractors) >= total_choices - 1:
                break
            label = format_label(car, mode)
            if label in seen_labels:
                continue
            distractors.append(car)
            seen_ids.add(car.id)
            seen_labels.add(label)
        if len(distractors) >= total_choices - 1:
            break

    # Fill remaining slots even if labels collide to guarantee total choices.
    if len(distractors) < total_choices - 1:
        remaining = [
            car
            for car in index.get_random_pool()
            if car.id not in seen_ids
        ]
        rng.shuffle(remaining)
        for car in remaining:
            if len(distractors) >= total_choices - 1:
                break
            distractors.append(car)
            seen_ids.add(car.id)

    choices = [correct] + distractors[: total_choices - 1]
    rng.shuffle(choices)

    return [AnswerChoice(id=car.id, label=format_label(car, mode), car=car) for car in choices]
