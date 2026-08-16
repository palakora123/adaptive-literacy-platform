"""Curriculum design: turn a placement result into an ordered learning plan."""
from __future__ import annotations

from sqlalchemy.orm import Session

import models
from content_library import module_spec
from leveling import MAX_LEVEL, SKILLS, band_for_level, clamp_level, level_label


def _ordered_skills(skill_levels: dict[str, int], overall: int) -> list[str]:
    """Weakest skill first, so the biggest gap gets attention while motivation is high.

    Ties break on the canonical SKILLS order rather than dict order, so two
    learners with identical results always get an identical plan.
    """
    return sorted(
        SKILLS,
        key=lambda s: (skill_levels.get(s, overall), SKILLS.index(s)),
    )


def build_plan(
    db: Session,
    *,
    user_id: int,
    level: int,
    skill_levels: dict[str, int],
    placement_session_id: int | None = None,
    rationale: str = "",
) -> models.CurriculumPlan:
    """Create an active curriculum plan with modules and lessons.

    Any previously active plan for this user is marked superseded, so a retaken
    placement test replaces the old plan instead of stacking beside it.
    """
    db.query(models.CurriculumPlan).filter(
        models.CurriculumPlan.user_id == user_id,
        models.CurriculumPlan.status == "active",
    ).update({"status": "superseded"}, synchronize_session=False)

    level = clamp_level(level)
    plan = models.CurriculumPlan(
        user_id=user_id,
        placement_session_id=placement_session_id,
        level=level,
        title=f"Level {level} Pathway - {level_label(level)}",
        rationale=rationale
        or (
            f"Built from your placement result. Modules run weakest skill first, "
            f"each pitched to move you from level {level} toward level "
            f"{min(MAX_LEVEL, level + 1)}."
        ),
        status="active",
    )
    db.add(plan)
    db.flush()  # assigns plan.id without committing

    for order, skill in enumerate(_ordered_skills(skill_levels, level)):
        start_level = clamp_level(skill_levels.get(skill, level))
        spec = module_spec(skill, band_for_level(start_level))

        module = models.CurriculumModule(
            plan_id=plan.id,
            order_index=order,
            skill_tag=skill,
            title=f"{skill}: {spec['title']}",
            objective=spec["objective"],
            start_level=start_level,
            target_level=min(MAX_LEVEL, start_level + 1),
            # Only the first module opens; the rest unlock as tests are passed.
            status="available" if order == 0 else "locked",
        )
        db.add(module)
        db.flush()

        for lesson_order, lesson in enumerate(spec["lessons"]):
            db.add(
                models.Lesson(
                    module_id=module.id,
                    order_index=lesson_order,
                    title=lesson["title"],
                    objective=lesson["objective"],
                    body_markdown=lesson["body"],
                    read_aloud_text=lesson["read_aloud"],
                    estimated_minutes=lesson["minutes"],
                )
            )

    db.commit()
    db.refresh(plan)
    return plan


def unlock_next_module(db: Session, module: models.CurriculumModule) -> None:
    """Open the module after `module`, if it is still locked."""
    nxt = (
        db.query(models.CurriculumModule)
        .filter(
            models.CurriculumModule.plan_id == module.plan_id,
            models.CurriculumModule.order_index == module.order_index + 1,
        )
        .first()
    )
    if nxt and nxt.status == "locked":
        nxt.status = "available"


def active_plan(db: Session, user_id: int) -> models.CurriculumPlan | None:
    return (
        db.query(models.CurriculumPlan)
        .filter(
            models.CurriculumPlan.user_id == user_id,
            models.CurriculumPlan.status == "active",
        )
        .order_by(models.CurriculumPlan.created_at.desc())
        .first()
    )
