from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

# --------------------------------------------------------------------------
# Auth
# --------------------------------------------------------------------------


class UserCreate(BaseModel):
    username: Optional[str] = None
    email: str
    password: str
    preferred_language: str = "en-IN"


class UserOut(BaseModel):
    id: int
    username: Optional[str] = None
    email: str
    level: Optional[int] = None
    placement_completed: bool = False
    preferred_language: str = "en-IN"
    model_config = ConfigDict(from_attributes=True)


class UserMe(UserOut):
    level_label: Optional[str] = None
    ability: Optional[float] = None
    has_curriculum: bool = False


class LanguagePreferenceUpdate(BaseModel):
    preferred_language: str


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Optional[str] = None


# --------------------------------------------------------------------------
# Legacy subject assessment (kept so existing subject tests keep working)
# --------------------------------------------------------------------------


class SubjectOut(BaseModel):
    id: int
    name: str
    description: str

    model_config = ConfigDict(from_attributes=True)


class QuestionOut(BaseModel):
    id: int
    subject_id: int
    question_text: str
    option_a: str
    option_b: str
    option_c: str
    option_d: str
    skill_tag: str
    difficulty: int = 5

    model_config = ConfigDict(from_attributes=True)


class AssessmentSubmit(BaseModel):
    answers: dict[int, str]  # question_id -> selected option ('A'..'D')


class DetailedResult(BaseModel):
    question_id: int
    question_text: str
    user_answer: str
    correct_answer: str
    is_correct: bool
    skill_tag: str
    explanation: Optional[str] = None


class AssessmentResult(BaseModel):
    score: int
    total_questions: int
    percentage: float
    category_breakdown: dict[str, float]
    strengths: list[str]
    weaknesses: list[str]
    detailed_results: list[DetailedResult]
    remarks: str
    actionable_feedback: list[str]


# --------------------------------------------------------------------------
# Adaptive placement test
# --------------------------------------------------------------------------


class PlacementQuestion(BaseModel):
    id: int
    question_text: str
    option_a: str
    option_b: str
    option_c: str
    option_d: str
    skill_tag: str
    difficulty: int


class PlacementProgress(BaseModel):
    answered: int
    min_questions: int
    max_questions: int
    # 0-1; the client shows this as a bar. Adaptive tests have no fixed length,
    # so it is a lower bound on how far through the learner is.
    fraction: float


class PlacementStep(BaseModel):
    session_id: int
    status: str  # in_progress | completed
    question: Optional[PlacementQuestion] = None
    progress: PlacementProgress
    # Populated only when status == "completed".
    level: Optional[int] = None
    level_label: Optional[str] = None


class PlacementAnswer(BaseModel):
    session_id: int
    question_id: int
    answer: str = Field(min_length=1, max_length=1)
    response_ms: Optional[int] = None
    via_voice: bool = False


class FocusArea(BaseModel):
    skill: str
    why_it_matters: str
    what_to_do: str


class StudyWeek(BaseModel):
    week: int
    focus: str
    activities: list[str]


class SkillBreakdown(BaseModel):
    skill: str
    level: int
    questions_answered: int
    correct: int


class ReportOut(BaseModel):
    placement_session_id: int
    level: int
    level_label: str
    ability: float
    standard_error: float
    questions_answered: int
    questions_correct: int
    skill_levels: list[SkillBreakdown]
    summary: str
    strengths: list[str]
    focus_areas: list[FocusArea]
    curriculum_rationale: str
    study_plan: list[StudyWeek]
    encouragement: str
    generated_by: str
    review: list[DetailedResult]
    curriculum_plan_id: Optional[int] = None


# --------------------------------------------------------------------------
# Curriculum and learning
# --------------------------------------------------------------------------


class LessonSummary(BaseModel):
    id: int
    order_index: int
    title: str
    objective: str
    estimated_minutes: int
    completed: bool


class LessonDetail(LessonSummary):
    module_id: int
    module_title: str
    skill_tag: str
    body_markdown: str
    read_aloud_text: Optional[str] = None
    next_lesson_id: Optional[int] = None
    prev_lesson_id: Optional[int] = None


class ModuleSummary(BaseModel):
    id: int
    order_index: int
    skill_tag: str
    title: str
    objective: str
    start_level: int
    target_level: int
    status: str
    best_score: Optional[float] = None
    lessons_total: int
    lessons_completed: int


class ModuleDetail(ModuleSummary):
    lessons: list[LessonSummary]
    attempts: list["PracticeAttemptOut"]


class CurriculumOut(BaseModel):
    plan_id: int
    title: str
    level: int
    level_label: str
    rationale: str
    modules: list[ModuleSummary]
    overall_progress: float


class PracticeAttemptOut(BaseModel):
    id: int
    score: int
    total: int
    percentage: float
    passed: bool
    level_before: Optional[int] = None
    level_after: Optional[int] = None
    taken_at: str


class PracticeTestOut(BaseModel):
    practice_session_id: int
    module_id: int
    module_title: str
    skill_tag: str
    pass_mark: int
    questions: list[PlacementQuestion]


class PracticeSubmit(BaseModel):
    practice_session_id: int
    answers: dict[int, str]


class PracticeResult(BaseModel):
    score: int
    total: int
    percentage: float
    passed: bool
    pass_mark: int
    module_status: str
    level_before: Optional[int] = None
    level_after: Optional[int] = None
    level_changed: bool
    next_module_id: Optional[int] = None
    feedback: str
    review: list[DetailedResult]


# --------------------------------------------------------------------------
# Voice
# --------------------------------------------------------------------------


class VoiceLanguage(BaseModel):
    code: str
    name: str
    native_name: str
    speech_code: str


class VoiceCapabilities(BaseModel):
    # False when SARVAM_API_KEY is unset; the client then uses Web Speech API.
    server_stt: bool
    server_tts: bool
    translation: bool
    auto_detect: bool
    languages: list[VoiceLanguage]
    default_language: str


class TranscriptionOut(BaseModel):
    transcript: str
    detected_language: Optional[str] = None
    translated_to_english: bool = False
    request_id: Optional[str] = None


class SpeakRequest(BaseModel):
    text: str
    language_code: str = "en-IN"
    speaker: Optional[str] = None


class SpeakOut(BaseModel):
    audios: list[str]  # base64-encoded WAV
    language_code: str
    speaker: str
    mime_type: str


class TranslateRequest(BaseModel):
    text: str
    source_language_code: str = "unknown"
    target_language_code: str = "en-IN"


class TranslateOut(BaseModel):
    translated_text: str
    source_language_code: str
    target_language_code: str


ModuleDetail.model_rebuild()
