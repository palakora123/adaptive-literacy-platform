from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, Float, Integer, String, Text

from database import Base


def _utcnow():
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)

    # Overall literacy level, 1-10. None until the placement test is finished.
    level = Column(Integer, nullable=True)
    # Continuous ability estimate behind `level`; kept so practice tests can
    # nudge the learner without snapping a whole level at a time.
    ability = Column(Float, nullable=True)
    placement_completed = Column(Boolean, default=False, nullable=False)
    # Preferred interface / voice language, e.g. "en-IN", "hi-IN".
    preferred_language = Column(String, default="en-IN", nullable=False)
    created_at = Column(DateTime(timezone=True), default=_utcnow)


class Subject(Base):
    __tablename__ = "subjects"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    description = Column(String)


class Question(Base):
    __tablename__ = "questions"
    id = Column(Integer, primary_key=True, index=True)
    subject_id = Column(Integer, index=True)
    question_text = Column(String)
    option_a = Column(String)
    option_b = Column(String)
    option_c = Column(String)
    option_d = Column(String)
    correct_option = Column(String)
    skill_tag = Column(String, index=True)
    # Calibrated difficulty on the same 1-10 scale as User.level.
    difficulty = Column(Integer, default=5, nullable=False, index=True)
    # Short teaching note shown in the answer review.
    explanation = Column(Text, nullable=True)


class AssessmentScore(Base):
    """Legacy flat-assessment result, kept so existing subject tests still work."""

    __tablename__ = "assessment_scores"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True)
    subject_id = Column(Integer, index=True)
    score = Column(Integer)
    timestamp = Column(String)
    category_scores_json = Column(String)


class PlacementSession(Base):
    """One adaptive placement run.

    Server-side state so the client cannot pick its own questions or replay
    answers. `asked_json` / `responses_json` hold the running item history.
    """

    __tablename__ = "placement_sessions"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True, nullable=False)
    status = Column(String, default="in_progress", nullable=False)  # in_progress | completed | abandoned
    # [question_id, ...] in the order served.
    asked_json = Column(Text, default="[]", nullable=False)
    # [{"question_id": int, "difficulty": int, "skill": str, "correct": bool,
    #   "answer": str, "response_ms": int|null, "via_voice": bool}, ...]
    responses_json = Column(Text, default="[]", nullable=False)
    ability = Column(Float, nullable=True)
    standard_error = Column(Float, nullable=True)
    level = Column(Integer, nullable=True)
    # {"Grammar": 4, "Vocabulary": 6, ...}
    skill_levels_json = Column(Text, nullable=True)
    started_at = Column(DateTime(timezone=True), default=_utcnow)
    completed_at = Column(DateTime(timezone=True), nullable=True)


class LiteracyReport(Base):
    """AI-generated (or rule-generated) narrative report for a placement run."""

    __tablename__ = "literacy_reports"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True, nullable=False)
    placement_session_id = Column(Integer, index=True, nullable=False)
    level = Column(Integer, nullable=False)
    level_label = Column(String, nullable=False)
    summary = Column(Text, nullable=False)
    strengths_json = Column(Text, nullable=False)
    # [{"skill": str, "why_it_matters": str, "what_to_do": str}, ...]
    focus_areas_json = Column(Text, nullable=False)
    curriculum_rationale = Column(Text, nullable=False)
    study_plan_json = Column(Text, nullable=False)
    encouragement = Column(Text, nullable=False)
    # "anthropic" when Claude wrote it, "rule_based" when the fallback did.
    generated_by = Column(String, default="rule_based", nullable=False)
    created_at = Column(DateTime(timezone=True), default=_utcnow)


class CurriculumPlan(Base):
    __tablename__ = "curriculum_plans"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True, nullable=False)
    placement_session_id = Column(Integer, index=True, nullable=True)
    level = Column(Integer, nullable=False)
    title = Column(String, nullable=False)
    rationale = Column(Text, nullable=False)
    status = Column(String, default="active", nullable=False)  # active | superseded
    created_at = Column(DateTime(timezone=True), default=_utcnow)


class CurriculumModule(Base):
    __tablename__ = "curriculum_modules"
    id = Column(Integer, primary_key=True, index=True)
    plan_id = Column(Integer, index=True, nullable=False)
    order_index = Column(Integer, nullable=False)
    skill_tag = Column(String, nullable=False)
    title = Column(String, nullable=False)
    objective = Column(Text, nullable=False)
    # Level the module teaches at, and the level the learner should reach.
    start_level = Column(Integer, nullable=False)
    target_level = Column(Integer, nullable=False)
    status = Column(String, default="locked", nullable=False)  # locked | available | in_progress | passed
    best_score = Column(Float, nullable=True)


class Lesson(Base):
    __tablename__ = "lessons"
    id = Column(Integer, primary_key=True, index=True)
    module_id = Column(Integer, index=True, nullable=False)
    order_index = Column(Integer, nullable=False)
    title = Column(String, nullable=False)
    objective = Column(String, nullable=False)
    body_markdown = Column(Text, nullable=False)
    # Sentence the learner reads aloud for pronunciation practice.
    read_aloud_text = Column(Text, nullable=True)
    estimated_minutes = Column(Integer, default=8, nullable=False)


class LessonProgress(Base):
    __tablename__ = "lesson_progress"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True, nullable=False)
    lesson_id = Column(Integer, index=True, nullable=False)
    completed_at = Column(DateTime(timezone=True), default=_utcnow)


class PracticeAttempt(Base):
    """A regular (non-placement) test taken against one curriculum module."""

    __tablename__ = "practice_attempts"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True, nullable=False)
    module_id = Column(Integer, index=True, nullable=False)
    skill_tag = Column(String, nullable=False)
    score = Column(Integer, nullable=False)
    total = Column(Integer, nullable=False)
    percentage = Column(Float, nullable=False)
    passed = Column(Boolean, default=False, nullable=False)
    level_before = Column(Integer, nullable=True)
    level_after = Column(Integer, nullable=True)
    taken_at = Column(DateTime(timezone=True), default=_utcnow)


class PracticeSession(Base):
    """Server-held answer key for an in-flight practice test."""

    __tablename__ = "practice_sessions"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True, nullable=False)
    module_id = Column(Integer, index=True, nullable=False)
    question_ids_json = Column(Text, nullable=False)
    status = Column(String, default="in_progress", nullable=False)
    created_at = Column(DateTime(timezone=True), default=_utcnow)
