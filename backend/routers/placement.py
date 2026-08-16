"""Adaptive placement test: serve one item at a time, then produce the report."""
from __future__ import annotations

import json
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

import ai_report
import config
import curriculum
import leveling
import models
import schemas
from auth import get_current_user
from database import get_db

router = APIRouter(prefix="/placement", tags=["placement"])


def _to_question(q: models.Question) -> schemas.PlacementQuestion:
    return schemas.PlacementQuestion(
        id=q.id,
        question_text=q.question_text,
        option_a=q.option_a,
        option_b=q.option_b,
        option_c=q.option_c,
        option_d=q.option_d,
        skill_tag=q.skill_tag,
        difficulty=q.difficulty,
    )


def _progress(answered: int) -> schemas.PlacementProgress:
    return schemas.PlacementProgress(
        answered=answered,
        min_questions=config.PLACEMENT_MIN_QUESTIONS,
        max_questions=config.PLACEMENT_MAX_QUESTIONS,
        fraction=min(1.0, answered / config.PLACEMENT_MAX_QUESTIONS),
    )


def _load(session: models.PlacementSession) -> tuple[list[int], list[dict]]:
    return json.loads(session.asked_json), json.loads(session.responses_json)


def _owned_session(
    db: Session, session_id: int, user: models.User
) -> models.PlacementSession:
    session = (
        db.query(models.PlacementSession)
        .filter(models.PlacementSession.id == session_id)
        .first()
    )
    if not session or session.user_id != user.id:
        # Same response for missing and not-yours, so session IDs cannot be probed.
        raise HTTPException(status_code=404, detail="Placement session not found")
    return session


def _serve_next(
    db: Session, session: models.PlacementSession
) -> schemas.PlacementStep:
    """Pick and record the next item, or finish the session."""
    asked, records = _load(session)
    responses = leveling.responses_from_records(records)
    ability, se = leveling.estimate_ability(responses) if responses else (5.0, 99.0)

    if leveling.should_stop(
        responses,
        se,
        config.PLACEMENT_MIN_QUESTIONS,
        config.PLACEMENT_MAX_QUESTIONS,
        config.PLACEMENT_TARGET_SE,
    ):
        return _finish(db, session, responses, ability, se)

    pool = db.query(models.Question).all()
    question = leveling.select_next_question(pool, responses, set(asked), ability)

    if question is None:
        # Bank exhausted - finish with whatever evidence we have rather than
        # leaving the learner stuck mid-test.
        return _finish(db, session, responses, ability, se)

    asked.append(question.id)
    session.asked_json = json.dumps(asked)
    session.ability = ability
    session.standard_error = se
    db.commit()

    return schemas.PlacementStep(
        session_id=session.id,
        status="in_progress",
        question=_to_question(question),
        progress=_progress(len(records)),
    )


def _finish(
    db: Session,
    session: models.PlacementSession,
    responses: list[leveling.Response],
    ability: float,
    se: float,
) -> schemas.PlacementStep:
    level = leveling.ability_to_level(ability)
    skill_levels = leveling.estimate_skill_levels(responses, ability)

    session.status = "completed"
    session.ability = ability
    session.standard_error = se
    session.level = level
    session.skill_levels_json = json.dumps(skill_levels)
    session.completed_at = datetime.now(timezone.utc)

    user = db.query(models.User).filter(models.User.id == session.user_id).first()
    if user:
        user.level = level
        user.ability = ability
        user.placement_completed = True
    db.commit()

    return schemas.PlacementStep(
        session_id=session.id,
        status="completed",
        question=None,
        progress=_progress(len(responses)),
        level=level,
        level_label=leveling.level_label(level),
    )


@router.post("/start", response_model=schemas.PlacementStep)
def start_placement(
    restart: bool = False,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Begin (or resume) an adaptive placement test.

    Resuming is the default so a refreshed browser does not lose progress.
    Pass `?restart=true` to abandon an in-flight session and start over.
    """
    existing = (
        db.query(models.PlacementSession)
        .filter(
            models.PlacementSession.user_id == current_user.id,
            models.PlacementSession.status == "in_progress",
        )
        .order_by(models.PlacementSession.started_at.desc())
        .first()
    )

    if existing and restart:
        existing.status = "abandoned"
        db.commit()
        existing = None

    if existing:
        asked, records = _load(existing)
        # Resume on the item that was served but never answered.
        if len(asked) > len(records):
            pending = (
                db.query(models.Question)
                .filter(models.Question.id == asked[-1])
                .first()
            )
            if pending:
                return schemas.PlacementStep(
                    session_id=existing.id,
                    status="in_progress",
                    question=_to_question(pending),
                    progress=_progress(len(records)),
                )
        return _serve_next(db, existing)

    if db.query(models.Question).count() == 0:
        raise HTTPException(
            status_code=503,
            detail="The question bank is empty. Run seed_db.py on the server.",
        )

    session = models.PlacementSession(user_id=current_user.id, status="in_progress")
    db.add(session)
    db.commit()
    db.refresh(session)
    return _serve_next(db, session)


@router.post("/answer", response_model=schemas.PlacementStep)
def answer_placement(
    payload: schemas.PlacementAnswer,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    session = _owned_session(db, payload.session_id, current_user)
    if session.status != "in_progress":
        raise HTTPException(status_code=409, detail="This test is already finished")

    asked, records = _load(session)

    if not asked or asked[-1] != payload.question_id:
        raise HTTPException(
            status_code=409,
            detail="That is not the question currently being asked.",
        )
    if any(r["question_id"] == payload.question_id for r in records):
        raise HTTPException(status_code=409, detail="Question already answered")

    question = (
        db.query(models.Question)
        .filter(models.Question.id == payload.question_id)
        .first()
    )
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")

    choice = payload.answer.strip().upper()
    if choice not in {"A", "B", "C", "D"}:
        raise HTTPException(status_code=400, detail="Answer must be A, B, C or D")

    records.append(
        {
            "question_id": question.id,
            "difficulty": question.difficulty,
            "skill": question.skill_tag,
            "correct": question.correct_option == choice,
            "answer": choice,
            "response_ms": payload.response_ms,
            "via_voice": payload.via_voice,
        }
    )
    session.responses_json = json.dumps(records)
    db.commit()

    return _serve_next(db, session)


def _build_report(
    db: Session, session: models.PlacementSession, user: models.User
) -> models.LiteracyReport:
    """Generate the report and curriculum for a completed session (idempotent)."""
    existing = (
        db.query(models.LiteracyReport)
        .filter(models.LiteracyReport.placement_session_id == session.id)
        .first()
    )
    if existing:
        return existing

    _, records = _load(session)
    skill_levels = json.loads(session.skill_levels_json or "{}")
    level = session.level or 5

    question_map = {
        q.id: q
        for q in db.query(models.Question)
        .filter(models.Question.id.in_([r["question_id"] for r in records] or [0]))
        .all()
    }
    enriched = [
        {
            "question_text": question_map[r["question_id"]].question_text,
            "skill": r["skill"],
            "difficulty": r["difficulty"],
            "correct": r["correct"],
        }
        for r in records
        if r["question_id"] in question_map
    ]

    # Build the curriculum first so the report can explain the actual module
    # order rather than inventing one.
    plan = curriculum.build_plan(
        db,
        user_id=user.id,
        level=level,
        skill_levels=skill_levels,
        placement_session_id=session.id,
    )
    modules = (
        db.query(models.CurriculumModule)
        .filter(models.CurriculumModule.plan_id == plan.id)
        .order_by(models.CurriculumModule.order_index)
        .all()
    )

    payload, generated_by = ai_report.generate_report(
        level=level,
        ability=session.ability or float(level),
        standard_error=session.standard_error or 0.0,
        skill_levels=skill_levels,
        responses=enriched,
        module_titles=[m.title for m in modules],
    )

    if generated_by == "anthropic" and payload.get("curriculum_rationale"):
        plan.rationale = payload["curriculum_rationale"]

    report = models.LiteracyReport(
        user_id=user.id,
        placement_session_id=session.id,
        level=level,
        level_label=leveling.level_label(level),
        summary=payload["summary"],
        strengths_json=json.dumps(payload["strengths"]),
        focus_areas_json=json.dumps(payload["focus_areas"]),
        curriculum_rationale=payload["curriculum_rationale"],
        study_plan_json=json.dumps(payload["study_plan"]),
        encouragement=payload["encouragement"],
        generated_by=generated_by,
    )
    db.add(report)
    db.commit()
    db.refresh(report)
    return report


def _report_response(
    db: Session, session: models.PlacementSession, report: models.LiteracyReport
) -> schemas.ReportOut:
    _, records = _load(session)
    skill_levels = json.loads(session.skill_levels_json or "{}")

    question_map = {
        q.id: q
        for q in db.query(models.Question)
        .filter(models.Question.id.in_([r["question_id"] for r in records] or [0]))
        .all()
    }

    review = [
        schemas.DetailedResult(
            question_id=r["question_id"],
            question_text=question_map[r["question_id"]].question_text,
            user_answer=r["answer"],
            correct_answer=question_map[r["question_id"]].correct_option,
            is_correct=r["correct"],
            skill_tag=r["skill"],
            explanation=question_map[r["question_id"]].explanation,
        )
        for r in records
        if r["question_id"] in question_map
    ]

    breakdown = [
        schemas.SkillBreakdown(
            skill=skill,
            level=lv,
            questions_answered=sum(1 for r in records if r["skill"] == skill),
            correct=sum(1 for r in records if r["skill"] == skill and r["correct"]),
        )
        for skill, lv in sorted(skill_levels.items(), key=lambda kv: -kv[1])
    ]

    plan = curriculum.active_plan(db, report.user_id)

    return schemas.ReportOut(
        placement_session_id=session.id,
        level=report.level,
        level_label=report.level_label,
        ability=session.ability or float(report.level),
        standard_error=session.standard_error or 0.0,
        questions_answered=len(records),
        questions_correct=sum(1 for r in records if r["correct"]),
        skill_levels=breakdown,
        summary=report.summary,
        strengths=json.loads(report.strengths_json),
        focus_areas=json.loads(report.focus_areas_json),
        curriculum_rationale=report.curriculum_rationale,
        study_plan=json.loads(report.study_plan_json),
        encouragement=report.encouragement,
        generated_by=report.generated_by,
        review=review,
        curriculum_plan_id=plan.id if plan else None,
    )


@router.get("/report/{session_id}", response_model=schemas.ReportOut)
def get_report(
    session_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Fetch (generating on first call) the AI report for a finished test."""
    session = _owned_session(db, session_id, current_user)
    if session.status != "completed":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Finish the placement test before requesting a report",
        )
    report = _build_report(db, session, current_user)
    return _report_response(db, session, report)


@router.get("/report", response_model=schemas.ReportOut)
def get_latest_report(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    session = (
        db.query(models.PlacementSession)
        .filter(
            models.PlacementSession.user_id == current_user.id,
            models.PlacementSession.status == "completed",
        )
        .order_by(models.PlacementSession.completed_at.desc())
        .first()
    )
    if not session:
        raise HTTPException(status_code=404, detail="No completed placement test yet")
    report = _build_report(db, session, current_user)
    return _report_response(db, session, report)
