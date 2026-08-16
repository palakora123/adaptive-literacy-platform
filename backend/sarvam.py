"""Sarvam AI client: multilingual speech-to-text, text-to-speech and translation.

The API key never reaches the browser - the frontend talks to our `/voice/*`
endpoints and this module is the only thing that holds the credential.

Every call is retried on transient failures and raises `SarvamError` with a
machine-readable `code` so the frontend can decide between showing an error,
retrying, and falling back to the browser's own Web Speech API.
"""
from __future__ import annotations

import base64
import logging
import time
from dataclasses import dataclass

import httpx

import config

log = logging.getLogger(__name__)


@dataclass(frozen=True)
class Language:
    code: str          # Sarvam language code, e.g. "hi-IN"
    name: str          # English name
    native_name: str   # Endonym, shown in the picker
    speech_code: str   # BCP-47 tag for the browser Web Speech API fallback
    tts_speaker: str   # Default Sarvam TTS voice


# Sarvam's supported Indic set plus Indian English. `speech_code` differs from
# `code` for Odia: Sarvam uses "od-IN", BCP-47 uses "or-IN".
LANGUAGES: list[Language] = [
    Language("en-IN", "English", "English", "en-IN", "anushka"),
    Language("hi-IN", "Hindi", "हिन्दी", "hi-IN", "anushka"),
    Language("bn-IN", "Bengali", "বাংলা", "bn-IN", "anushka"),
    Language("gu-IN", "Gujarati", "ગુજરાતી", "gu-IN", "anushka"),
    Language("kn-IN", "Kannada", "ಕನ್ನಡ", "kn-IN", "anushka"),
    Language("ml-IN", "Malayalam", "മലയാളം", "ml-IN", "anushka"),
    Language("mr-IN", "Marathi", "मराठी", "mr-IN", "anushka"),
    Language("od-IN", "Odia", "ଓଡ଼ିଆ", "or-IN", "anushka"),
    Language("pa-IN", "Punjabi", "ਪੰਜਾਬੀ", "pa-IN", "anushka"),
    Language("ta-IN", "Tamil", "தமிழ்", "ta-IN", "anushka"),
    Language("te-IN", "Telugu", "తెలుగు", "te-IN", "anushka"),
]

LANGUAGE_CODES = {lang.code for lang in LANGUAGES}
# Sarvam's sentinel asking the model to detect the language itself.
AUTO_DETECT = "unknown"

_BY_CODE = {lang.code: lang for lang in LANGUAGES}


def get_language(code: str) -> Language | None:
    return _BY_CODE.get(code)


def normalise_language(code: str | None, *, allow_auto: bool = True) -> str:
    """Coerce a client-supplied language code to something Sarvam accepts."""
    if not code:
        return AUTO_DETECT if allow_auto else "en-IN"
    code = code.strip()
    if code in LANGUAGE_CODES:
        return code
    if allow_auto and code in {AUTO_DETECT, "auto", ""}:
        return AUTO_DETECT
    # Accept a bare tag like "hi" or a BCP-47 variant like "or-IN".
    prefix = code.split("-")[0].lower()
    aliases = {"or": "od-IN"}
    if prefix in aliases:
        return aliases[prefix]
    for lang in LANGUAGES:
        if lang.code.split("-")[0] == prefix:
            return lang.code
    return AUTO_DETECT if allow_auto else "en-IN"


class SarvamError(Exception):
    def __init__(self, code: str, message: str, *, status: int = 502):
        super().__init__(message)
        self.code = code
        self.message = message
        self.status = status


class SarvamNotConfigured(SarvamError):
    def __init__(self) -> None:
        super().__init__(
            "not_configured",
            "Sarvam AI is not configured on the server. Set SARVAM_API_KEY to "
            "enable server-side speech recognition.",
            status=503,
        )


def _headers() -> dict[str, str]:
    if not config.SARVAM_API_KEY:
        raise SarvamNotConfigured()
    return {"api-subscription-key": config.SARVAM_API_KEY}


def _request(
    method: str,
    path: str,
    *,
    json_body: dict | None = None,
    data: dict | None = None,
    files: dict | None = None,
) -> dict:
    """Issue a Sarvam request with bounded retries on transient failures."""
    url = f"{config.SARVAM_BASE_URL}{path}"
    headers = _headers()
    last_error: SarvamError | None = None

    for attempt in range(config.SARVAM_MAX_RETRIES + 1):
        try:
            with httpx.Client(timeout=config.SARVAM_TIMEOUT_SECONDS) as client:
                response = client.request(
                    method, url, headers=headers, json=json_body, data=data, files=files
                )
        except httpx.TimeoutException:
            last_error = SarvamError(
                "timeout", "Speech service timed out. Please try again.", status=504
            )
        except httpx.HTTPError as exc:
            last_error = SarvamError(
                "network", f"Could not reach the speech service: {exc}", status=502
            )
        else:
            if response.status_code == 200:
                try:
                    return response.json()
                except ValueError:
                    raise SarvamError(
                        "bad_response", "Speech service returned malformed data."
                    ) from None

            # 4xx other than 429 will not succeed on retry - fail immediately.
            if response.status_code == 401 or response.status_code == 403:
                raise SarvamError(
                    "unauthorized",
                    "Speech service rejected the server's credentials.",
                    status=502,
                )
            if response.status_code == 429:
                last_error = SarvamError(
                    "rate_limited",
                    "Speech service is busy. Please try again in a moment.",
                    status=429,
                )
            elif 400 <= response.status_code < 500:
                detail = response.text[:300]
                raise SarvamError(
                    "invalid_request",
                    f"Speech service rejected the request: {detail}",
                    status=400,
                )
            else:
                last_error = SarvamError(
                    "upstream_error",
                    f"Speech service error ({response.status_code}).",
                    status=502,
                )

        if attempt < config.SARVAM_MAX_RETRIES:
            # Exponential backoff: 0.5s, then 1.0s.
            time.sleep(0.5 * (2 ** attempt))

    raise last_error or SarvamError("unknown", "Speech service failed.")


# --------------------------------------------------------------------------
# Speech to text
# --------------------------------------------------------------------------

def transcribe(
    audio_bytes: bytes,
    filename: str,
    content_type: str,
    *,
    language_code: str = AUTO_DETECT,
    translate_to_english: bool = False,
) -> dict:
    """Transcribe audio.

    With `translate_to_english`, Sarvam's speech-to-text-translate endpoint
    detects the spoken language and returns English text - which is what makes
    a learner able to answer an English comprehension question in Marathi.
    """
    if not audio_bytes:
        raise SarvamError("empty_audio", "No audio was received.", status=400)
    if len(audio_bytes) > config.VOICE_MAX_UPLOAD_BYTES:
        raise SarvamError(
            "audio_too_large",
            "That recording is too long. Keep it under about a minute.",
            status=413,
        )

    files = {"file": (filename or "audio.webm", audio_bytes, content_type or "audio/webm")}

    if translate_to_english:
        payload = _request(
            "POST",
            "/speech-to-text-translate",
            data={"model": "saaras:v2"},
            files=files,
        )
    else:
        payload = _request(
            "POST",
            "/speech-to-text",
            data={
                "model": config.SARVAM_STT_MODEL,
                "language_code": language_code or AUTO_DETECT,
            },
            files=files,
        )

    transcript = (payload.get("transcript") or "").strip()
    detected = payload.get("language_code") or (
        None if language_code == AUTO_DETECT else language_code
    )
    return {
        "transcript": transcript,
        "detected_language": detected,
        "translated_to_english": translate_to_english,
        "request_id": payload.get("request_id"),
    }


# --------------------------------------------------------------------------
# Text to speech
# --------------------------------------------------------------------------

# Sarvam rejects very long TTS inputs; split on sentence boundaries.
_TTS_CHUNK_CHARS = 450


def _chunk_text(text: str, size: int = _TTS_CHUNK_CHARS) -> list[str]:
    text = text.strip()
    if len(text) <= size:
        return [text]

    chunks: list[str] = []
    current = ""
    for sentence in text.replace("\n", " ").split(". "):
        piece = sentence if sentence.endswith(".") else sentence + "."
        if len(current) + len(piece) + 1 > size and current:
            chunks.append(current.strip())
            current = piece
        else:
            current = f"{current} {piece}".strip()
    if current:
        chunks.append(current.strip())
    # A single sentence longer than the limit still needs a hard cut.
    return [c[:size] for c in chunks if c]


def synthesize(text: str, *, language_code: str = "en-IN", speaker: str | None = None) -> dict:
    """Return base64 WAV audio for `text`."""
    text = (text or "").strip()
    if not text:
        raise SarvamError("empty_text", "There is nothing to read aloud.", status=400)

    language_code = normalise_language(language_code, allow_auto=False)
    lang = get_language(language_code)
    voice = speaker or (lang.tts_speaker if lang else "anushka")

    audios: list[str] = []
    for chunk in _chunk_text(text):
        payload = _request(
            "POST",
            "/text-to-speech",
            json_body={
                "text": chunk,
                "target_language_code": language_code,
                "speaker": voice,
                "model": config.SARVAM_TTS_MODEL,
            },
        )
        audios.extend(payload.get("audios") or [])

    if not audios:
        raise SarvamError("no_audio", "Speech service returned no audio.")

    # Validate the payload is real base64 before handing it to an <audio> tag.
    try:
        base64.b64decode(audios[0], validate=True)
    except Exception:  # noqa: BLE001
        raise SarvamError("bad_response", "Speech service returned invalid audio.") from None

    return {
        "audios": audios,
        "language_code": language_code,
        "speaker": voice,
        "mime_type": "audio/wav",
    }


# --------------------------------------------------------------------------
# Translation
# --------------------------------------------------------------------------

def translate(
    text: str, *, source_language_code: str = AUTO_DETECT, target_language_code: str = "en-IN"
) -> dict:
    """Translate text between any two supported languages."""
    text = (text or "").strip()
    if not text:
        raise SarvamError("empty_text", "There is nothing to translate.", status=400)

    target = normalise_language(target_language_code, allow_auto=False)
    source = normalise_language(source_language_code, allow_auto=True)

    payload = _request(
        "POST",
        "/translate",
        json_body={
            "input": text[:1000],
            "source_language_code": source,
            "target_language_code": target,
            "model": config.SARVAM_TRANSLATE_MODEL,
            "mode": "formal",
        },
    )
    return {
        "translated_text": payload.get("translated_text", ""),
        "source_language_code": payload.get("source_language_code", source),
        "target_language_code": target,
    }
