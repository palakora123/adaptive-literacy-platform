"""AI-generated literacy report.

Claude writes the narrative report and curriculum recommendation from the
structured placement result. Everything degrades to a deterministic rule-based
report when no API key is configured, when the SDK is missing, or when the call
fails - a learner must never be blocked from their results by an outage.
"""
from __future__ import annotations

import json
import logging
from typing import Any

import config
from leveling import SKILLS, band_name, level_label

log = logging.getLogger(__name__)

# Set once if the installed SDK predates the server-side fallback parameter, so
# we stop retrying a call shape this environment cannot make.
_fallbacks_supported = True


REPORT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "summary": {
            "type": "string",
            "description": (
                "3-5 sentences addressed to the learner as 'you', describing what "
                "their placement result means in practical terms."
            ),
        },
        "strengths": {
            "type": "array",
            "items": {"type": "string"},
            "description": "2-4 specific strengths, each one short sentence.",
        },
        "focus_areas": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "skill": {"type": "string"},
                    "why_it_matters": {
                        "type": "string",
                        "description": "One sentence on the real-world cost of this gap.",
                    },
                    "what_to_do": {
                        "type": "string",
                        "description": "One concrete, doable practice action.",
                    },
                },
                "required": ["skill", "why_it_matters", "what_to_do"],
                "additionalProperties": False,
            },
            "description": "2-4 areas of improvement, weakest first.",
        },
        "curriculum_rationale": {
            "type": "string",
            "description": (
                "2-4 sentences explaining why the recommended module order suits "
                "this learner specifically."
            ),
        },
        "study_plan": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "week": {"type": "integer"},
                    "focus": {"type": "string"},
                    "activities": {"type": "array", "items": {"type": "string"}},
                },
                "required": ["week", "focus", "activities"],
                "additionalProperties": False,
            },
            "description": "A 4-week plan, one entry per week, 2-3 activities each.",
        },
        "encouragement": {
            "type": "string",
            "description": "One or two warm, specific, non-generic closing sentences.",
        },
    },
    "required": [
        "summary",
        "strengths",
        "focus_areas",
        "curriculum_rationale",
        "study_plan",
        "encouragement",
    ],
    "additionalProperties": False,
}


SYSTEM_PROMPT = """\
You are the assessment analyst for an adult literacy learning platform. You turn \
a completed adaptive placement test into a report the learner reads themselves, \
immediately after finishing the test.

The platform places learners on a 1-10 literacy scale:

  1-2  Foundation - decoding everyday words, simple sentences
  3-4  Developing - short texts, basic tenses, common punctuation
  5-6  Proficient - workplace texts, complex sentences, register
  7-8  Advanced - argument, inference, nuance, formal writing
  9-10 Mastery - dense specialist prose, rhetorical control, editorial judgement

Skills assessed: Vocabulary, Grammar, Reading Comprehension, Punctuation, Spelling.

How to write the report:

- Address the learner directly as "you". Never refer to them in the third person \
and never mention that you are an AI.
- Be specific to this result. Name the actual skills and levels. A report that \
would fit any learner is a failed report.
- The level is a starting point, not a verdict. Say so through the content, not \
by asserting it.
- Ground every claim in the data you are given. If a skill has few items, treat \
its level as provisional and say so rather than over-reading it.
- Focus areas are ranked weakest first, and each needs one concrete action the \
learner could start today - not "practise more".
- Keep the register plain and warm. A learner at level 2 must be able to read \
their own report, so match the vocabulary to the measured level.
- No emoji, no exclamation marks, no motivational cliches.
"""


def _band_guidance(level: int) -> str:
    return {
        "foundation": (
            "This learner is at foundation level. Use very short sentences and "
            "common words throughout the whole report. Avoid any word you would "
            "not expect in the 1000 most frequent English words."
        ),
        "developing": (
            "This learner is at developing level. Use plain, direct language and "
            "keep sentences under about 20 words."
        ),
        "proficient": (
            "This learner reads competently. Normal plain English is fine."
        ),
        "advanced": (
            "This learner is advanced. You can be precise and analytical, and "
            "should be specific about the fine distinctions they are missing."
        ),
        "mastery": (
            "This learner is near-expert. Be exacting: their remaining gaps are "
            "narrow, so vague encouragement will read as unearned. Name precise "
            "residual weaknesses."
        ),
    }[band_name(level)]


def _build_user_prompt(
    *,
    level: int,
    ability: float,
    standard_error: float,
    skill_levels: dict[str, int],
    responses: list[dict],
    module_titles: list[str],
) -> str:
    correct = sum(1 for r in responses if r["correct"])
    total = len(responses)

    missed = [
        f"  - [{r['skill']}, difficulty {r['difficulty']}] {r['question_text']}"
        for r in responses
        if not r["correct"]
    ]
    passed_hard = sorted(
        (r for r in responses if r["correct"]),
        key=lambda r: -r["difficulty"],
    )[:3]

    skill_lines = "\n".join(
        f"  - {skill}: level {skill_levels.get(skill, level)} "
        f"({sum(1 for r in responses if r['skill'] == skill)} items answered)"
        for skill in SKILLS
        if skill in skill_levels
    )

    return f"""\
Placement result for one learner.

OVERALL
  Level: {level} of 10 ({level_label(level)})
  Ability estimate: {ability} (standard error {standard_error})
  Score: {correct} of {total} adaptive items correct

PER-SKILL LEVELS
{skill_lines}

HARDEST ITEMS ANSWERED CORRECTLY
{chr(10).join(f"  - [{r['skill']}, difficulty {r['difficulty']}] {r['question_text']}" for r in passed_hard) or "  (none)"}

ITEMS ANSWERED INCORRECTLY
{chr(10).join(missed) or "  (none - the learner answered every item correctly)"}

RECOMMENDED MODULE SEQUENCE (already generated by the platform; explain it, do not redesign it)
{chr(10).join(f"  {i + 1}. {t}" for i, t in enumerate(module_titles)) or "  (none)"}

WRITING LEVEL FOR THIS REPORT
{_band_guidance(level)}

Write the report now."""


def _call_claude(system: str, user_prompt: str) -> dict[str, Any] | None:
    global _fallbacks_supported

    try:
        import anthropic
    except ImportError:
        log.warning("anthropic SDK not installed; using rule-based report")
        return None

    client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY, timeout=90.0)

    request: dict[str, Any] = {
        "model": config.ANTHROPIC_MODEL,
        "max_tokens": 8000,
        "output_config": {
            "effort": config.ANTHROPIC_EFFORT,
            "format": {"type": "json_schema", "schema": REPORT_SCHEMA},
        },
        # The system prompt is byte-stable across learners, so it caches and
        # every report after the first reads it at ~10% of input cost.
        "system": [
            {"type": "text", "text": system, "cache_control": {"type": "ephemeral"}}
        ],
        "messages": [{"role": "user", "content": user_prompt}],
    }

    def _invoke(use_fallbacks: bool):
        if use_fallbacks:
            return client.beta.messages.create(
                betas=["server-side-fallback-2026-07-01"],
                fallbacks="default",
                **request,
            )
        return client.messages.create(**request)

    try:
        try:
            response = _invoke(_fallbacks_supported)
        except TypeError:
            # Installed SDK does not know the `fallbacks` parameter.
            _fallbacks_supported = False
            response = _invoke(False)

        if response.stop_reason == "refusal":
            log.warning("Report generation refused by safety classifiers")
            return None

        text = "".join(
            block.text for block in response.content if block.type == "text"
        )
        if not text.strip():
            return None
        return json.loads(text)

    except Exception:  # noqa: BLE001 - any failure falls back to rules
        log.exception("Claude report generation failed; using rule-based report")
        return None


# --------------------------------------------------------------------------
# Deterministic fallback
# --------------------------------------------------------------------------

_SKILL_ADVICE = {
    "Vocabulary": (
        "Vocabulary gaps slow down everything else you read, because an unknown "
        "word stops the sentence.",
        "Keep a notebook of words you had to reread, with the sentence they came "
        "from, and review it twice a week.",
    ),
    "Grammar": (
        "Grammar errors make writing harder to trust, even when the content is "
        "right.",
        "Rewrite three sentences from something you read today, changing the "
        "tense each time, and check whether the meaning still holds.",
    ),
    "Reading Comprehension": (
        "Comprehension is what turns reading into understanding; without it, you "
        "finish a page without keeping anything.",
        "After each paragraph you read, close your eyes and say its main point in "
        "one sentence before moving on.",
    ),
    "Punctuation": (
        "Punctuation controls where a reader pauses, so weak punctuation makes "
        "clear thinking look muddled.",
        "Take a paragraph you wrote, read it aloud, and place a mark everywhere "
        "you naturally paused - then check whether one belongs there.",
    ),
    "Spelling": (
        "Spelling errors are the first thing a reader notices and the easiest "
        "thing to fix.",
        "Collect your own misspellings for a week, group them by pattern, and "
        "drill only the two patterns that appear most.",
    ),
}


def _rule_based_report(
    *,
    level: int,
    skill_levels: dict[str, int],
    responses: list[dict],
    module_titles: list[str],
) -> dict[str, Any]:
    correct = sum(1 for r in responses if r["correct"])
    total = max(1, len(responses))
    ranked = sorted(skill_levels.items(), key=lambda kv: kv[1])
    weakest = [s for s, lv in ranked if lv <= level][:3] or [ranked[0][0]]
    strongest = [s for s, lv in reversed(ranked) if lv >= level][:3]

    strengths = [
        f"{skill} is your strongest strand, holding at level {skill_levels[skill]}."
        for skill in strongest
    ] or ["You completed the full adaptive test, which is the hardest part to start."]

    focus_areas = []
    for skill in weakest:
        why, what = _SKILL_ADVICE.get(
            skill,
            (
                f"{skill} is holding back your overall level.",
                f"Spend fifteen minutes a day on {skill} exercises.",
            ),
        )
        focus_areas.append(
            {"skill": skill, "why_it_matters": why, "what_to_do": what}
        )

    summary = (
        f"You placed at level {level} of 10 ({level_label(level)}), answering "
        f"{correct} of {total} adaptive questions correctly. The test adjusts to "
        f"you as you go, so a level {level} result means you were consistently "
        f"handling material pitched at that difficulty. Your strongest area is "
        f"{strongest[0] if strongest else weakest[0]}, and the clearest gap is "
        f"{weakest[0]}. This is a starting point for your curriculum, not a "
        f"final score - it will be re-checked as you complete practice tests."
    )

    study_plan = []
    for week in range(1, 5):
        skill = weakest[(week - 1) % len(weakest)]
        study_plan.append(
            {
                "week": week,
                "focus": skill,
                "activities": [
                    f"Work through the {skill} lessons in your curriculum.",
                    f"Take the {skill} practice test and review every wrong answer.",
                    "Read aloud for ten minutes using the voice practice tool.",
                ],
            }
        )

    return {
        "summary": summary,
        "strengths": strengths,
        "focus_areas": focus_areas,
        "curriculum_rationale": (
            "Your curriculum starts with "
            f"{module_titles[0] if module_titles else 'your weakest skill'} because "
            "the placement test found the biggest gap there, and later modules build "
            "on it. Each module is pitched one level above where you currently sit, "
            "which is far enough to stretch you without being discouraging."
        ),
        "study_plan": study_plan,
        "encouragement": (
            f"A level {level} start is a real measurement of where you are today, "
            "and every module you finish moves it. Take the practice tests even "
            "when you are unsure - that is how the platform learns what to give "
            "you next."
        ),
    }


def generate_report(
    *,
    level: int,
    ability: float,
    standard_error: float,
    skill_levels: dict[str, int],
    responses: list[dict],
    module_titles: list[str],
) -> tuple[dict[str, Any], str]:
    """Return (report_dict, generated_by).

    `responses` items need: question_text, skill, difficulty, correct.
    """
    if config.AI_REPORTS_ENABLED:
        prompt = _build_user_prompt(
            level=level,
            ability=ability,
            standard_error=standard_error,
            skill_levels=skill_levels,
            responses=responses,
            module_titles=module_titles,
        )
        result = _call_claude(SYSTEM_PROMPT, prompt)
        if result:
            return result, "anthropic"

    return (
        _rule_based_report(
            level=level,
            skill_levels=skill_levels,
            responses=responses,
            module_titles=module_titles,
        ),
        "rule_based",
    )
