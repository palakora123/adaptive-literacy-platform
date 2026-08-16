"""Ability estimation and adaptive item selection for the placement test.

We use a one-parameter logistic (Rasch) model expressed directly on the 1-10
level scale, so ability and item difficulty are the same units:

    P(correct | theta, d) = 1 / (1 + exp(-DISCRIMINATION * (theta - d)))

Ability is estimated by maximum likelihood over a fine grid. The grid is small
enough (about 200 points) that a closed-form Newton step buys nothing, and the
grid never diverges on all-correct / all-wrong response patterns the way
Newton-Raphson does.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Iterable, Sequence

MIN_LEVEL = 1
MAX_LEVEL = 10

# How sharply the probability of a correct answer rises around the item's
# difficulty. 1.1 gives roughly a 75% success rate one level below an item.
DISCRIMINATION = 1.1

# Grid bounds extend half a level past the scale so that a perfect or empty
# score still lands on a defensible interior estimate.
_GRID = [MIN_LEVEL - 0.5 + 0.05 * i for i in range(int((MAX_LEVEL + 1.0) / 0.05) + 1)]

SKILLS = [
    "Vocabulary",
    "Grammar",
    "Reading Comprehension",
    "Punctuation",
    "Spelling",
]

LEVEL_LABELS = {
    1: "Emerging Reader",
    2: "Early Foundation",
    3: "Building Basics",
    4: "Developing Reader",
    5: "Competent Everyday Reader",
    6: "Confident Communicator",
    7: "Proficient Reader",
    8: "Advanced Reader",
    9: "Highly Advanced",
    10: "Expert / Near-Native",
}

BAND_NAMES = {
    1: "foundation",   # levels 1-2
    2: "developing",   # levels 3-4
    3: "proficient",   # levels 5-6
    4: "advanced",     # levels 7-8
    5: "mastery",      # levels 9-10
}


@dataclass(frozen=True)
class Response:
    question_id: int
    difficulty: int
    skill: str
    correct: bool


def band_for_level(level: int) -> int:
    """Map a 1-10 level onto one of five content bands."""
    level = clamp_level(level)
    return (level + 1) // 2


def band_name(level: int) -> str:
    return BAND_NAMES[band_for_level(level)]


def level_label(level: int) -> str:
    return LEVEL_LABELS[clamp_level(level)]


def clamp_level(level: int) -> int:
    return max(MIN_LEVEL, min(MAX_LEVEL, int(level)))


def _p_correct(theta: float, difficulty: float) -> float:
    # Guard the exponent so extreme grid points cannot overflow.
    z = max(-30.0, min(30.0, DISCRIMINATION * (theta - difficulty)))
    return 1.0 / (1.0 + math.exp(-z))


def _log_likelihood(theta: float, responses: Sequence[Response]) -> float:
    total = 0.0
    for r in responses:
        p = _p_correct(theta, r.difficulty)
        # Clamp away from 0/1 so log() stays finite.
        p = min(max(p, 1e-9), 1 - 1e-9)
        total += math.log(p) if r.correct else math.log(1 - p)
    return total


def _information(theta: float, responses: Sequence[Response]) -> float:
    """Fisher information; its reciprocal square root is the standard error."""
    total = 0.0
    for r in responses:
        p = _p_correct(theta, r.difficulty)
        total += (DISCRIMINATION ** 2) * p * (1 - p)
    return total


def estimate_ability(responses: Sequence[Response]) -> tuple[float, float]:
    """Return (ability, standard_error) for a set of responses.

    An all-correct or all-wrong pattern has no interior maximum, so the grid
    search would pin to a boundary. We instead anchor those cases to the
    hardest item passed (or easiest item failed) with a one-level margin,
    which is the standard "extreme score" adjustment.
    """
    if not responses:
        return 5.0, 99.0

    n_correct = sum(1 for r in responses if r.correct)

    if n_correct == len(responses):
        hardest = max(r.difficulty for r in responses)
        ability = min(float(MAX_LEVEL), hardest + 1.0)
    elif n_correct == 0:
        easiest = min(r.difficulty for r in responses)
        ability = max(float(MIN_LEVEL), easiest - 1.0)
    else:
        ability = max(_GRID, key=lambda t: _log_likelihood(t, responses))

    info = _information(ability, responses)
    se = 1.0 / math.sqrt(info) if info > 1e-9 else 99.0
    return round(ability, 3), round(se, 3)


def ability_to_level(ability: float) -> int:
    """Round an ability estimate onto the 1-10 integer scale."""
    return clamp_level(int(round(ability)))


def estimate_skill_levels(
    responses: Sequence[Response], overall_ability: float
) -> dict[str, int]:
    """Per-skill levels, shrunk toward the overall estimate when data is thin.

    With only two or three items per skill a raw per-skill estimate is very
    noisy, so we blend it with the overall ability by a weight that grows with
    the item count. At six-plus items the skill estimate stands on its own.
    """
    by_skill: dict[str, list[Response]] = {}
    for r in responses:
        by_skill.setdefault(r.skill, []).append(r)

    levels: dict[str, int] = {}
    for skill, items in by_skill.items():
        skill_ability, _ = estimate_ability(items)
        weight = min(1.0, len(items) / 6.0)
        blended = weight * skill_ability + (1 - weight) * overall_ability
        levels[skill] = ability_to_level(blended)
    return levels


def select_next_question(
    candidates: Iterable,
    responses: Sequence[Response],
    asked_ids: set[int],
    ability: float,
) -> object | None:
    """Pick the most informative unseen item, balancing skill coverage.

    Ranking is by (skill already covered?, |difficulty - ability|), so an
    under-tested skill wins ties and the test never spends all 20 items on one
    strand. `candidates` is any iterable of ORM Question rows.
    """
    seen_per_skill: dict[str, int] = {s: 0 for s in SKILLS}
    for r in responses:
        seen_per_skill[r.skill] = seen_per_skill.get(r.skill, 0) + 1

    best = None
    best_key: tuple[int, float, int] | None = None

    for q in candidates:
        if q.id in asked_ids:
            continue
        coverage = seen_per_skill.get(q.skill_tag, 0)
        distance = abs(q.difficulty - ability)
        # Deterministic tiebreak on id keeps the sequence reproducible.
        key = (coverage, distance, q.id)
        if best_key is None or key < best_key:
            best, best_key = q, key

    return best


def should_stop(
    responses: Sequence[Response],
    standard_error: float,
    min_questions: int,
    max_questions: int,
    target_se: float,
) -> bool:
    n = len(responses)
    if n >= max_questions:
        return True
    if n < min_questions:
        return False
    return standard_error <= target_se


def responses_from_records(records: Iterable[dict]) -> list[Response]:
    return [
        Response(
            question_id=int(r["question_id"]),
            difficulty=int(r["difficulty"]),
            skill=str(r["skill"]),
            correct=bool(r["correct"]),
        )
        for r in records
    ]


def apply_practice_result(
    current_ability: float, difficulty: float, percentage: float, weight: float = 0.35
) -> float:
    """Nudge a learner's ability after a practice test.

    A practice test is short and single-skill, so it moves the overall estimate
    only partway toward what that score implies - full re-estimation is the
    placement test's job. Scoring 100% at difficulty d implies roughly d + 1;
    scoring 50% implies roughly d.
    """
    implied = difficulty + (percentage - 50.0) / 50.0
    blended = (1 - weight) * current_ability + weight * implied
    return round(max(float(MIN_LEVEL), min(float(MAX_LEVEL), blended)), 3)
