"""Curriculum browsing, lesson delivery and the regular practice tests."""
from __future__ import annotations

import json
import random

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

import config
import curriculum
import leveling
import models
import schemas
from auth import get_current_user
from database import get_db

router = APIRouter(tags=["learning"])

# Percentage needed to pass a module test and unlock the next module.
PASS_MARK = 70


# --------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------


def _require_plan(db: Session, user: models.User) -> models.CurriculumPlan:
    plan = curriculum.active_plan(db, user.id)
    if not plan:
        raise HTTPException(
            status_code=404,
            detail="No curriculum yet. Complete the placement test first.",
        )
    return plan


def _completed_lesson_ids(db: Session, user_id: int) -> set[int]:
    return {
        row.lesson_id
        for row in db.query(models.LessonProgress)
        .filter(models.LessonProgress.user_id == user_id)
        .all()
    }


def _module_summary(
    module: models.CurriculumModule, lessons: list[models.Lesson], done: set[int]
) -> schemas.ModuleSummary:
    return schemas.ModuleSummary(
        id=module.id,
        order_index=module.order_index,
        skill_tag=module.skill_tag,
        title=module.title,
        objective=module.objective,
        start_level=module.start_level,
        target_level=module.target_level,
        status=module.status,
        best_score=module.best_score,
        lessons_total=len(lessons),
        lessons_completed=sum(1 for l in lessons if l.id in done),
    )


def _owned_module(
    db: Session, module_id: int, user: models.User
) -> models.CurriculumModule:
    module = (
        db.query(models.CurriculumModule)
        .filter(models.CurriculumModule.id == module_id)
        .first()
    )
    if not module:
        raise HTTPException(status_code=404, detail="Module not found")
    plan = (
        db.query(models.CurriculumPlan)
        .filter(models.CurriculumPlan.id == module.plan_id)
        .first()
    )
    if not plan or plan.user_id != user.id:
        raise HTTPException(status_code=404, detail="Module not found")
    return module


def _attempt_out(a: models.PracticeAttempt) -> schemas.PracticeAttemptOut:
    return schemas.PracticeAttemptOut(
        id=a.id,
        score=a.score,
        total=a.total,
        percentage=round(a.percentage, 1),
        passed=a.passed,
        level_before=a.level_before,
        level_after=a.level_after,
        taken_at=a.taken_at.isoformat() if a.taken_at else "",
    )


# --------------------------------------------------------------------------
# Curriculum
# --------------------------------------------------------------------------


@router.get("/curriculum", response_model=schemas.CurriculumOut)
def get_curriculum(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    plan = _require_plan(db, current_user)
    modules = (
        db.query(models.CurriculumModule)
        .filter(models.CurriculumModule.plan_id == plan.id)
        .order_by(models.CurriculumModule.order_index)
        .all()
    )
    done = _completed_lesson_ids(db, current_user.id)

    summaries: list[schemas.ModuleSummary] = []
    total_lessons = 0
    total_done = 0
    for module in modules:
        lessons = (
            db.query(models.Lesson)
            .filter(models.Lesson.module_id == module.id)
            .order_by(models.Lesson.order_index)
            .all()
        )
        total_lessons += len(lessons)
        total_done += sum(1 for l in lessons if l.id in done)
        summaries.append(_module_summary(module, lessons, done))

    # Passing the module test is half the work; reading the lessons is the other
    # half, so progress weights both rather than counting lessons alone.
    lesson_fraction = (total_done / total_lessons) if total_lessons else 0.0
    passed_fraction = (
        sum(1 for m in modules if m.status == "passed") / len(modules)
        if modules
        else 0.0
    )

    return schemas.CurriculumOut(
        plan_id=plan.id,
        title=plan.title,
        level=plan.level,
        level_label=leveling.level_label(plan.level),
        rationale=plan.rationale,
        modules=summaries,
        overall_progress=round(0.5 * lesson_fraction + 0.5 * passed_fraction, 3),
    )


@router.get("/curriculum/modules/{module_id}", response_model=schemas.ModuleDetail)
def get_module(
    module_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    module = _owned_module(db, module_id, current_user)
    lessons = (
        db.query(models.Lesson)
        .filter(models.Lesson.module_id == module.id)
        .order_by(models.Lesson.order_index)
        .all()
    )
    done = _completed_lesson_ids(db, current_user.id)
    attempts = (
        db.query(models.PracticeAttempt)
        .filter(
            models.PracticeAttempt.user_id == current_user.id,
            models.PracticeAttempt.module_id == module.id,
        )
        .order_by(models.PracticeAttempt.taken_at.desc())
        .limit(10)
        .all()
    )

    summary = _module_summary(module, lessons, done)
    return schemas.ModuleDetail(
        **summary.model_dump(),
        lessons=[
            schemas.LessonSummary(
                id=l.id,
                order_index=l.order_index,
                title=l.title,
                objective=l.objective,
                estimated_minutes=l.estimated_minutes,
                completed=l.id in done,
            )
            for l in lessons
        ],
        attempts=[_attempt_out(a) for a in attempts],
    )


# --------------------------------------------------------------------------
# Lessons
# --------------------------------------------------------------------------


@router.get("/lessons/{lesson_id}", response_model=schemas.LessonDetail)
def get_lesson(
    lesson_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    lesson = db.query(models.Lesson).filter(models.Lesson.id == lesson_id).first()
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")
    module = _owned_module(db, lesson.module_id, current_user)

    siblings = (
        db.query(models.Lesson)
        .filter(models.Lesson.module_id == module.id)
        .order_by(models.Lesson.order_index)
        .all()
    )
    index = next(i for i, l in enumerate(siblings) if l.id == lesson.id)
    done = _completed_lesson_ids(db, current_user.id)

    return schemas.LessonDetail(
        id=lesson.id,
        order_index=lesson.order_index,
        title=lesson.title,
        objective=lesson.objective,
        estimated_minutes=lesson.estimated_minutes,
        completed=lesson.id in done,
        module_id=module.id,
        module_title=module.title,
        skill_tag=module.skill_tag,
        body_markdown=lesson.body_markdown,
        read_aloud_text=lesson.read_aloud_text,
        prev_lesson_id=siblings[index - 1].id if index > 0 else None,
        next_lesson_id=(
            siblings[index + 1].id if index + 1 < len(siblings) else None
        ),
    )


@router.post("/lessons/{lesson_id}/complete", response_model=schemas.LessonSummary)
def complete_lesson(
    lesson_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    lesson = db.query(models.Lesson).filter(models.Lesson.id == lesson_id).first()
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")
    module = _owned_module(db, lesson.module_id, current_user)

    already = (
        db.query(models.LessonProgress)
        .filter(
            models.LessonProgress.user_id == current_user.id,
            models.LessonProgress.lesson_id == lesson.id,
        )
        .first()
    )
    if not already:
        db.add(
            models.LessonProgress(user_id=current_user.id, lesson_id=lesson.id)
        )
        if module.status == "available":
            module.status = "in_progress"
        db.commit()

    return schemas.LessonSummary(
        id=lesson.id,
        order_index=lesson.order_index,
        title=lesson.title,
        objective=lesson.objective,
        estimated_minutes=lesson.estimated_minutes,
        completed=True,
    )


# --------------------------------------------------------------------------
# Regular practice tests
# --------------------------------------------------------------------------


def _pick_practice_questions(
    db: Session, module: models.CurriculumModule, exclude_ids: set[int]
) -> list[models.Question]:
    """Draw a test around the module's target level for its skill.

    Items are sampled from a window centred on the target level so a test mixes
    consolidation with a genuine stretch, rather than being uniformly hard.
    """
    target = module.target_level
    pool = (
        db.query(models.Question)
        .filter(models.Question.skill_tag == module.skill_tag)
        .all()
    )
    if not pool:
        return []

    def bucket(q: models.Question) -> int:
        return abs(q.difficulty - target)

    fresh = [q for q in pool if q.id not in exclude_ids]
    # Fall back to the full pool once the learner has seen everything, rather
    # than serving a short test.
    source = fresh if len(fresh) >= config.PRACTICE_TEST_LENGTH else pool

    ranked = sorted(source, key=lambda q: (bucket(q), q.id))
    window = ranked[: max(config.PRACTICE_TEST_LENGTH * 2, config.PRACTICE_TEST_LENGTH)]
    chosen = random.sample(window, min(config.PRACTICE_TEST_LENGTH, len(window)))
    return sorted(chosen, key=lambda q: q.difficulty)


@router.post("/practice/{module_id}/start", response_model=schemas.PracticeTestOut)
def start_practice(
    module_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    module = _owned_module(db, module_id, current_user)
    if module.status == "locked":
        raise HTTPException(
            status_code=403,
            detail="Finish the earlier modules before taking this test.",
        )

    seen = {
        qid
        for row in db.query(models.PracticeSession)
        .filter(
            models.PracticeSession.user_id == current_user.id,
            models.PracticeSession.module_id == module.id,
        )
        .all()
        for qid in json.loads(row.question_ids_json)
    }
    questions = _pick_practice_questions(db, module, seen)
    if not questions:
        raise HTTPException(
            status_code=503,
            detail=f"No {module.skill_tag} questions available for this test.",
        )

    session = models.PracticeSession(
        user_id=current_user.id,
        module_id=module.id,
        question_ids_json=json.dumps([q.id for q in questions]),
    )
    db.add(session)
    db.commit()
    db.refresh(session)

    return schemas.PracticeTestOut(
        practice_session_id=session.id,
        module_id=module.id,
        module_title=module.title,
        skill_tag=module.skill_tag,
        pass_mark=PASS_MARK,
        questions=[
            schemas.PlacementQuestion(
                id=q.id,
                question_text=q.question_text,
                option_a=q.option_a,
                option_b=q.option_b,
                option_c=q.option_c,
                option_d=q.option_d,
                skill_tag=q.skill_tag,
                difficulty=q.difficulty,
            )
            for q in questions
        ],
    )


@router.post("/practice/submit", response_model=schemas.PracticeResult)
def submit_practice(
    payload: schemas.PracticeSubmit,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    session = (
        db.query(models.PracticeSession)
        .filter(models.PracticeSession.id == payload.practice_session_id)
        .first()
    )
    if not session or session.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Practice session not found")
    if session.status != "in_progress":
        raise HTTPException(status_code=409, detail="This test was already submitted")

    module = _owned_module(db, session.module_id, current_user)
    question_ids = json.loads(session.question_ids_json)
    questions = {
        q.id: q
        for q in db.query(models.Question)
        .filter(models.Question.id.in_(question_ids))
        .all()
    }

    review: list[schemas.DetailedResult] = []
    score = 0
    for qid in question_ids:
        question = questions.get(qid)
        if not question:
            continue
        given = (payload.answers.get(qid) or "").strip().upper()
        correct = given == question.correct_option
        if correct:
            score += 1
        review.append(
            schemas.DetailedResult(
                question_id=qid,
                question_text=question.question_text,
                user_answer=given or "-",
                correct_answer=question.correct_option,
                is_correct=correct,
                skill_tag=question.skill_tag,
                explanation=question.explanation,
            )
        )

    total = len(review)
    percentage = (score / total * 100) if total else 0.0
    passed = percentage >= PASS_MARK

    level_before = current_user.level
    ability_before = current_user.ability if current_user.ability is not None else float(
        current_user.level or 5
    )
    ability_after = leveling.apply_practice_result(
        ability_before, float(module.target_level), percentage
    )
    level_after = leveling.ability_to_level(ability_after)

    current_user.ability = ability_after
    current_user.level = level_after

    module.best_score = max(module.best_score or 0.0, percentage)
    next_module_id = None
    if passed:
        module.status = "passed"
        curriculum.unlock_next_module(db, module)
        nxt = (
            db.query(models.CurriculumModule)
            .filter(
                models.CurriculumModule.plan_id == module.plan_id,
                models.CurriculumModule.order_index == module.order_index + 1,
            )
            .first()
        )
        next_module_id = nxt.id if nxt else None
    elif module.status == "available":
        module.status = "in_progress"

    session.status = "completed"
    db.add(
        models.PracticeAttempt(
            user_id=current_user.id,
            module_id=module.id,
            skill_tag=module.skill_tag,
            score=score,
            total=total,
            percentage=percentage,
            passed=passed,
            level_before=level_before,
            level_after=level_after,
        )
    )
    db.commit()

    if passed and level_after != (level_before or level_after):
        feedback = (
            f"Passed with {percentage:.0f}%. Your overall level moved from "
            f"{level_before} to {level_after}, and the next module is now open."
        )
    elif passed:
        feedback = (
            f"Passed with {percentage:.0f}%. The next module is now open. Your "
            f"overall level is holding at {level_after}."
        )
    else:
        weakest = next((r.skill_tag for r in review if not r.is_correct), module.skill_tag)
        feedback = (
            f"You scored {percentage:.0f}%, and {PASS_MARK}% unlocks the next "
            f"module. Review the {weakest} lessons and the explanations below, "
            f"then retake it - retakes draw fresh questions."
        )

    return schemas.PracticeResult(
        score=score,
        total=total,
        percentage=round(percentage, 1),
        passed=passed,
        pass_mark=PASS_MARK,
        module_status=module.status,
        level_before=level_before,
        level_after=level_after,
        level_changed=level_before != level_after,
        next_module_id=next_module_id,
        feedback=feedback,
        review=review,
    )
