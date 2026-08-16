import json
from datetime import datetime, timedelta, timezone

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

import config
import curriculum
import leveling
import models
import sarvam
import schemas
from auth import create_access_token, get_current_user, get_password_hash, verify_password
from database import engine, get_db
from routers import learn, placement, voice

models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Literacy Assistant API",
    description=(
        "Adaptive literacy placement (levels 1-10), AI-generated reports, "
        "personalised curriculum with regular tests, and multilingual voice "
        "input powered by Sarvam AI."
    ),
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(placement.router)
app.include_router(learn.router)
app.include_router(voice.router)


@app.get("/")
def read_root():
    return {
        "Status": "Backend is running successfully",
        "Project": "Literacy Assistant",
        "features": {
            "adaptive_placement": True,
            "ai_reports": config.AI_REPORTS_ENABLED,
            "voice": config.VOICE_ENABLED,
        },
    }


# --------------------------------------------------------------------------
# Auth
# --------------------------------------------------------------------------


@app.post(
    "/register",
    response_model=schemas.UserOut,
    status_code=status.HTTP_201_CREATED,
    tags=["auth"],
)
def register(user: schemas.UserCreate, db: Session = Depends(get_db)):
    if db.query(models.User).filter(models.User.email == user.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")

    db_user = models.User(
        username=user.username,
        email=user.email,
        hashed_password=get_password_hash(user.password),
        preferred_language=sarvam.normalise_language(
            user.preferred_language, allow_auto=False
        ),
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


@app.post("/token", response_model=schemas.Token, tags=["auth"])
def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)
):
    user = (
        db.query(models.User)
        .filter(models.User.email == form_data.username)
        .first()
    )
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(
        data={"sub": user.email},
        expires_delta=timedelta(minutes=config.ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/me", response_model=schemas.UserMe, tags=["auth"])
def read_me(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Everything the shell needs to route a user: level, placement state, plan."""
    plan = curriculum.active_plan(db, current_user.id)
    return schemas.UserMe(
        id=current_user.id,
        username=current_user.username,
        email=current_user.email,
        level=current_user.level,
        placement_completed=current_user.placement_completed,
        preferred_language=current_user.preferred_language or "en-IN",
        level_label=(
            leveling.level_label(current_user.level) if current_user.level else None
        ),
        ability=current_user.ability,
        has_curriculum=plan is not None,
    )


# --------------------------------------------------------------------------
# Legacy flat subject assessment
#
# Superseded by /placement for levelling, but kept working so existing subject
# tests and their saved scores remain usable.
# --------------------------------------------------------------------------


@app.get("/subjects", response_model=list[schemas.SubjectOut], tags=["assessments"])
def get_subjects(db: Session = Depends(get_db)):
    return db.query(models.Subject).all()


@app.get(
    "/assessments/{subject_id}",
    response_model=list[schemas.QuestionOut],
    tags=["assessments"],
)
def get_questions(
    subject_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    questions = (
        db.query(models.Question)
        .filter(models.Question.subject_id == subject_id)
        .order_by(models.Question.difficulty, models.Question.id)
        .all()
    )
    if not questions:
        raise HTTPException(
            status_code=404, detail="No questions found for this subject"
        )
    return questions


@app.post(
    "/assessments/{subject_id}/submit",
    response_model=schemas.AssessmentResult,
    tags=["assessments"],
)
def submit_assessment(
    subject_id: int,
    submission: schemas.AssessmentSubmit,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    questions = (
        db.query(models.Question)
        .filter(models.Question.subject_id == subject_id)
        .all()
    )
    if not questions:
        raise HTTPException(status_code=404, detail="Subject or questions not found")

    question_map = {q.id: q for q in questions}
    total_questions = len(questions)
    score = 0

    category_stats: dict[str, dict[str, int]] = {}
    for q in questions:
        category_stats.setdefault(q.skill_tag, {"total": 0, "correct": 0})
        category_stats[q.skill_tag]["total"] += 1

    detailed_results = []
    for str_q_id, answer in submission.answers.items():
        q_id = int(str_q_id)
        q = question_map.get(q_id)
        if not q:
            continue
        is_correct = q.correct_option == answer
        if is_correct:
            score += 1
            category_stats[q.skill_tag]["correct"] += 1
        detailed_results.append(
            {
                "question_id": q.id,
                "question_text": q.question_text,
                "user_answer": answer,
                "correct_answer": q.correct_option,
                "is_correct": is_correct,
                "skill_tag": q.skill_tag,
                "explanation": q.explanation,
            }
        )

    percentage = (score / total_questions) * 100 if total_questions else 0

    category_breakdown: dict[str, float] = {}
    strengths: list[str] = []
    weaknesses: list[str] = []
    for cat, stats in category_stats.items():
        pct = (stats["correct"] / stats["total"]) * 100 if stats["total"] else 0.0
        category_breakdown[cat] = pct
        (strengths if pct >= 70 else weaknesses).append(cat)

    if percentage >= 90:
        remarks = "Outstanding! You have an excellent grasp of the concepts."
    elif percentage >= 75:
        remarks = (
            "Great job! You have a solid understanding, with just a few areas to polish."
        )
    elif percentage >= 50:
        remarks = (
            "Good effort. You have a foundational understanding, but there is room "
            "for improvement."
        )
    else:
        remarks = (
            "Keep practicing! Reviewing the core concepts will help you build a "
            "stronger foundation."
        )

    advice = {
        "Grammar": "Review sentence structure, verb tenses, and subject-verb agreement rules.",
        "Vocabulary": "Read more extensively and practice using new words in context.",
        "Reading Comprehension": "Practice reading longer passages and summarising the main ideas.",
        "Punctuation": "Focus on comma placement, semicolons, and proper sentence boundaries.",
        "Spelling": "Collect your own misspellings for a week and drill the two commonest patterns.",
    }
    actionable_feedback = [
        advice.get(w, f"Dedicate some time to reviewing {w} fundamentals.")
        for w in weaknesses
    ] or [
        "You did great across all categories! Challenge yourself with advanced "
        "materials next."
    ]

    db.add(
        models.AssessmentScore(
            user_id=current_user.id,
            subject_id=subject_id,
            score=score,
            timestamp=datetime.now(timezone.utc).isoformat(),
            category_scores_json=json.dumps(category_breakdown),
        )
    )
    db.commit()

    return {
        "score": score,
        "total_questions": total_questions,
        "percentage": percentage,
        "category_breakdown": category_breakdown,
        "strengths": strengths,
        "weaknesses": weaknesses,
        "detailed_results": detailed_results,
        "remarks": remarks,
        "actionable_feedback": actionable_feedback,
    }
