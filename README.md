# Literacy Assistant

An adaptive literacy platform: a placement test grades a new user onto a 1-10
level, an AI-written report explains the result and recommends a curriculum,
and a module-based learning platform with regular tests takes it from there.
Voice input and output are powered by Sarvam AI across English and ten Indic
languages, with a browser-based fallback when Sarvam isn't configured.

## What's here

| Layer | Stack |
|---|---|
| Backend | FastAPI + SQLAlchemy + PostgreSQL |
| Frontend | Next.js 16 (App Router) + TypeScript + Tailwind |
| AI report | Claude (Anthropic API), with a deterministic rule-based fallback |
| Voice | Sarvam AI (STT / TTS / translation), with a Web Speech API fallback |

## How the pieces fit together

1. **Placement** (`/placement`) — an adaptive test (Rasch/1PL model in
   `backend/leveling.py`) picks one question at a time from a 100-item bank
   spanning difficulty 1-10 across five skills (Vocabulary, Grammar, Reading
   Comprehension, Punctuation, Spelling). It stops as soon as the ability
   estimate is precise enough (12-20 questions), never fixed-length.
2. **Report** (`/report`) — `backend/ai_report.py` sends the placement result
   to Claude with a `json_schema` output format and gets back a structured
   report: summary, strengths, ranked focus areas, curriculum rationale, a
   4-week study plan, and encouragement. Without `ANTHROPIC_API_KEY` set, a
   rule-based generator produces an equivalent (less personalized) report so
   the feature never blocks on missing credentials.
3. **Curriculum** (`/learn`) — `backend/curriculum.py` turns the placement
   result into an ordered set of modules, weakest skill first, each with
   three lessons drawn from `backend/content_library.py` (75 hand-written
   lessons across 5 skills x 5 difficulty bands). Modules unlock in sequence.
4. **Practice tests** (`/practice/[moduleId]`) — each module ends with an
   8-question test drawn fresh every attempt from a window around the
   module's target difficulty. Passing (≥70%) unlocks the next module and
   nudges the learner's overall level.
5. **Voice** — `backend/sarvam.py` wraps Sarvam's STT/TTS/translate APIs with
   retries and typed errors. The frontend's `VoiceInput` and `SpeakButton`
   components use it when available and fall back to the browser's own
   `SpeechRecognition` / `speechSynthesis` otherwise, always telling the user
   which engine is in use.

## Setup

### Backend

```bash
cd backend
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
cp .env.example .env   # fill in DATABASE_URL at minimum
# create the postgres role/db referenced by DATABASE_URL, then:
.venv/bin/python seed_db.py   # drops and reseeds the schema + question bank
.venv/bin/uvicorn main:app --reload --port 8000
```

`ANTHROPIC_API_KEY` and `SARVAM_API_KEY` are both optional — see
`backend/.env.example`. Without them the app runs with rule-based reports and
browser-only voice, which is a fully working (if less capable) experience.

### Frontend

```bash
cd frontend
npm install
npm run dev
```

The dev server proxies `/api/*` to `http://127.0.0.1:8000` (see
`next.config.ts`) so the browser never needs the backend's origin directly.

### First run

1. Register an account at `/register`.
2. You're routed straight into `/placement` — answer honestly, by typing or
   by voice.
3. On completion you land on `/report`, then `/learn` for your curriculum.

## Notes for reviewers

- `backend/leveling.py` has no external dependencies and is unit-testable in
  isolation — it's the only place the 1-10 scale math lives.
- The legacy flat assessment (`/subjects`, `/assessments/{id}`) from the
  original codebase still works unmodified; it's superseded by `/placement`
  but nothing was deleted.
- `frontend/hooks/useVoiceRecorder.ts` and `components/voice/*` are the
  voice layer; they're independent of the assessment/curriculum logic and
  reusable anywhere text input is accepted.
