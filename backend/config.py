"""Runtime configuration, read from the environment with safe defaults.

Nothing here is required for the app to boot. Missing AI or voice credentials
degrade those features gracefully rather than crashing the API.
"""
import os


def _flag(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


# --- Database -------------------------------------------------------------
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://admin:password123@localhost/literacy_app",
)

# --- Auth -----------------------------------------------------------------
SECRET_KEY = os.getenv(
    "SECRET_KEY",
    "super-secret-key-for-literacy-app-please-change-in-prod",
)
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))

# --- CORS -----------------------------------------------------------------
CORS_ORIGINS = [
    o.strip()
    for o in os.getenv(
        "CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000"
    ).split(",")
    if o.strip()
]

# --- Anthropic (AI report + curriculum rationale) -------------------------
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-opus-5")
# Bounded, structured generation - "medium" keeps report latency acceptable for
# a synchronous web request. Raise to "high" if report quality matters more.
ANTHROPIC_EFFORT = os.getenv("ANTHROPIC_EFFORT", "medium")
AI_REPORTS_ENABLED = _flag("AI_REPORTS_ENABLED", default=True) and bool(ANTHROPIC_API_KEY)

# --- Sarvam AI (multilingual speech) --------------------------------------
SARVAM_API_KEY = os.getenv("SARVAM_API_KEY")
SARVAM_BASE_URL = os.getenv("SARVAM_BASE_URL", "https://api.sarvam.ai").rstrip("/")
SARVAM_STT_MODEL = os.getenv("SARVAM_STT_MODEL", "saarika:v2.5")
SARVAM_TTS_MODEL = os.getenv("SARVAM_TTS_MODEL", "bulbul:v2")
SARVAM_TRANSLATE_MODEL = os.getenv("SARVAM_TRANSLATE_MODEL", "mayura:v1")
SARVAM_TIMEOUT_SECONDS = float(os.getenv("SARVAM_TIMEOUT_SECONDS", "30"))
SARVAM_MAX_RETRIES = int(os.getenv("SARVAM_MAX_RETRIES", "2"))
# Hard ceiling on uploaded audio so a bad client cannot exhaust memory.
VOICE_MAX_UPLOAD_BYTES = int(os.getenv("VOICE_MAX_UPLOAD_BYTES", str(10 * 1024 * 1024)))

VOICE_ENABLED = bool(SARVAM_API_KEY)

# --- Assessment tuning ----------------------------------------------------
PLACEMENT_MIN_QUESTIONS = int(os.getenv("PLACEMENT_MIN_QUESTIONS", "12"))
PLACEMENT_MAX_QUESTIONS = int(os.getenv("PLACEMENT_MAX_QUESTIONS", "20"))
# Stop early once the ability estimate is this precise (in level units).
PLACEMENT_TARGET_SE = float(os.getenv("PLACEMENT_TARGET_SE", "0.45"))
PRACTICE_TEST_LENGTH = int(os.getenv("PRACTICE_TEST_LENGTH", "8"))
