"""Sarvam AI voice endpoints.

The browser never sees the Sarvam key. When the key is not configured, these
endpoints report `server_stt: false` via `/voice/capabilities` so the client can
switch to the browser's Web Speech API instead of failing silently.
"""
from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

import config
import models
import sarvam
import schemas
from auth import get_current_user
from database import get_db

log = logging.getLogger(__name__)
router = APIRouter(prefix="/voice", tags=["voice"])


def _http_error(exc: sarvam.SarvamError) -> HTTPException:
    return HTTPException(
        status_code=exc.status,
        detail={"code": exc.code, "message": exc.message},
    )


@router.get("/capabilities", response_model=schemas.VoiceCapabilities)
def capabilities(current_user: models.User = Depends(get_current_user)):
    """What the voice layer can do right now, and in which languages.

    The client calls this on mount and uses it to decide whether to render the
    Sarvam-backed recorder or the browser fallback.
    """
    return schemas.VoiceCapabilities(
        server_stt=config.VOICE_ENABLED,
        server_tts=config.VOICE_ENABLED,
        translation=config.VOICE_ENABLED,
        auto_detect=config.VOICE_ENABLED,
        languages=[
            schemas.VoiceLanguage(
                code=l.code,
                name=l.name,
                native_name=l.native_name,
                speech_code=l.speech_code,
            )
            for l in sarvam.LANGUAGES
        ],
        default_language=current_user.preferred_language or "en-IN",
    )


@router.post("/transcribe", response_model=schemas.TranscriptionOut)
async def transcribe(
    audio: UploadFile = File(...),
    language_code: str = Form(sarvam.AUTO_DETECT),
    translate_to_english: bool = Form(False),
    current_user: models.User = Depends(get_current_user),
):
    """Transcribe a recording.

    `language_code` may be "unknown" to let Sarvam detect it. Setting
    `translate_to_english` returns English text regardless of what was spoken,
    which is how a learner answers an English question in their own language.
    """
    if not config.VOICE_ENABLED:
        raise _http_error(sarvam.SarvamNotConfigured())

    # Read with a hard cap so an oversized upload cannot exhaust memory.
    data = await audio.read(config.VOICE_MAX_UPLOAD_BYTES + 1)
    if len(data) > config.VOICE_MAX_UPLOAD_BYTES:
        raise HTTPException(
            status_code=413,
            detail={
                "code": "audio_too_large",
                "message": "That recording is too long. Keep it under about a minute.",
            },
        )

    try:
        result = sarvam.transcribe(
            data,
            audio.filename or "audio.webm",
            audio.content_type or "audio/webm",
            language_code=sarvam.normalise_language(language_code),
            translate_to_english=translate_to_english,
        )
    except sarvam.SarvamError as exc:
        raise _http_error(exc) from exc

    return schemas.TranscriptionOut(**result)


@router.post("/speak", response_model=schemas.SpeakOut)
def speak(
    payload: schemas.SpeakRequest,
    current_user: models.User = Depends(get_current_user),
):
    """Read text aloud - used for questions, lessons and pronunciation models."""
    if not config.VOICE_ENABLED:
        raise _http_error(sarvam.SarvamNotConfigured())
    try:
        result = sarvam.synthesize(
            payload.text,
            language_code=payload.language_code,
            speaker=payload.speaker,
        )
    except sarvam.SarvamError as exc:
        raise _http_error(exc) from exc
    return schemas.SpeakOut(**result)


@router.post("/translate", response_model=schemas.TranslateOut)
def translate(
    payload: schemas.TranslateRequest,
    current_user: models.User = Depends(get_current_user),
):
    """Translate text, e.g. to show a question in the learner's first language."""
    if not config.VOICE_ENABLED:
        raise _http_error(sarvam.SarvamNotConfigured())
    try:
        result = sarvam.translate(
            payload.text,
            source_language_code=payload.source_language_code,
            target_language_code=payload.target_language_code,
        )
    except sarvam.SarvamError as exc:
        raise _http_error(exc) from exc
    return schemas.TranslateOut(**result)


@router.put("/language", response_model=schemas.UserOut)
def set_language(
    payload: schemas.LanguagePreferenceUpdate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    code = sarvam.normalise_language(payload.preferred_language, allow_auto=False)
    current_user.preferred_language = code
    db.commit()
    db.refresh(current_user)
    return current_user
