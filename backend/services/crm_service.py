from __future__ import annotations

from datetime import date, datetime, time, timezone
from typing import Any, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from backend.models import FollowUp, HCP, Interaction


LIST_FIELDS = {"attendees", "topics", "materials_shared", "samples_distributed", "follow_up_actions"}
INTERACTION_FIELDS = {
    "interaction_type",
    "date",
    "time",
    "attendees",
    "topics",
    "materials_shared",
    "samples_distributed",
    "sentiment",
    "outcome",
    "follow_up_actions",
    "summary",
}


def get_or_create_hcp(db: Session, name: str, specialty: Optional[str] = None) -> HCP:
    stmt = select(HCP).where(HCP.name.ilike(name))
    hcp = db.execute(stmt).scalar_one_or_none()
    if hcp:
        return hcp
    hcp = HCP(name=name, specialty=specialty)
    db.add(hcp)
    db.flush()
    return hcp


def create_interaction(db: Session, data: dict[str, Any]) -> Interaction:
    payload = _normalize_interaction_payload(data)
    hcp = _resolve_hcp(db, payload)
    interaction = Interaction(
        hcp_id=hcp.id,
        interaction_type=payload.get("interaction_type") or "meeting",
        date=payload.get("date"),
        time=payload.get("time"),
        attendees=payload.get("attendees", []),
        topics=payload.get("topics", []),
        materials_shared=payload.get("materials_shared", []),
        samples_distributed=payload.get("samples_distributed", []),
        sentiment=payload.get("sentiment"),
        outcome=payload.get("outcome"),
        follow_up_actions=payload.get("follow_up_actions", []),
        summary=payload.get("summary"),
    )
    db.add(interaction)
    db.commit()
    db.refresh(interaction)
    return interaction


def get_interaction(db: Session, interaction_id: int) -> Optional[Interaction]:
    return db.execute(
        select(Interaction)
        .options(joinedload(Interaction.hcp))
        .where(Interaction.id == interaction_id)
    ).scalar_one_or_none()


def list_interactions(db: Session, limit: int = 50) -> list[Interaction]:
    return list(
        db.execute(
            select(Interaction)
            .options(joinedload(Interaction.hcp))
            .order_by(Interaction.created_at.desc())
            .limit(limit)
        ).scalars()
    )


def delete_interaction(db: Session, interaction_id: int) -> bool:
    interaction = get_interaction(db, interaction_id)
    if not interaction:
        return False
    db.delete(interaction)
    db.commit()
    return True


def delete_all_interactions(db: Session) -> int:
    interactions = list(db.execute(select(Interaction)).scalars())
    count = len(interactions)
    for interaction in interactions:
        db.delete(interaction)
    db.commit()
    return count


def update_interaction(db: Session, interaction_id: int, updates: dict[str, Any]) -> Optional[Interaction]:
    interaction = get_interaction(db, interaction_id)
    if not interaction:
        return None
    normalized = _normalize_interaction_payload(updates, partial=True)
    for field, value in normalized.items():
        if field in INTERACTION_FIELDS:
            setattr(interaction, field, value)
    # Explicitly set updated_at so it works with both PostgreSQL and SQLite
    interaction.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(interaction)
    return interaction


def search_hcps(db: Session, query: str) -> list[HCP]:
    pattern = f"%{query}%"
    return list(db.execute(select(HCP).where(HCP.name.ilike(pattern)).order_by(HCP.name)).scalars())


def interactions_for_hcp(db: Session, hcp_id: int) -> list[Interaction]:
    return list(
        db.execute(
            select(Interaction)
            .options(joinedload(Interaction.hcp))
            .where(Interaction.hcp_id == hcp_id)
            .order_by(Interaction.date.desc().nullslast(), Interaction.created_at.desc())
        ).scalars()
    )


def create_followup(db: Session, interaction_id: int, scheduled_date: date, note: str) -> FollowUp:
    followup = FollowUp(interaction_id=interaction_id, scheduled_date=scheduled_date, note=note)
    db.add(followup)
    db.commit()
    db.refresh(followup)
    return followup


def list_followups(db: Session) -> list[FollowUp]:
    return list(
        db.execute(
            select(FollowUp)
            .options(joinedload(FollowUp.interaction).joinedload(Interaction.hcp))
            .order_by(FollowUp.scheduled_date.asc())
        ).scalars()
    )


def serialize_interaction(interaction: Interaction) -> dict[str, Any]:
    return {
        "id": interaction.id,
        "hcp_id": interaction.hcp_id,
        "hcp_name": interaction.hcp.name if interaction.hcp else "",
        "interaction_type": interaction.interaction_type,
        "date": interaction.date.isoformat() if interaction.date else None,
        "time": interaction.time.isoformat() if interaction.time else None,
        "attendees": interaction.attendees or [],
        "topics": interaction.topics or [],
        "materials_shared": interaction.materials_shared or [],
        "samples_distributed": interaction.samples_distributed or [],
        "sentiment": interaction.sentiment,
        "outcome": interaction.outcome,
        "follow_up_actions": interaction.follow_up_actions or [],
        "summary": interaction.summary,
        "created_at": interaction.created_at.isoformat() if interaction.created_at else None,
        "updated_at": interaction.updated_at.isoformat() if interaction.updated_at else None,
    }


def serialize_followup(followup: FollowUp) -> dict[str, Any]:
    interaction = followup.interaction
    hcp_name = interaction.hcp.name if interaction and interaction.hcp else ""
    return {
        "id": followup.id,
        "interaction_id": followup.interaction_id,
        "hcp_name": hcp_name,
        "scheduled_date": followup.scheduled_date.isoformat(),
        "note": followup.note,
        "status": followup.status,
        "created_at": followup.created_at.isoformat() if followup.created_at else None,
    }


def _resolve_hcp(db: Session, payload: dict[str, Any]) -> HCP:
    hcp_id = payload.get("hcp_id")
    if hcp_id:
        hcp = db.get(HCP, hcp_id)
        if hcp:
            return hcp
    hcp_name = payload.get("hcp_name") or "Unknown HCP"
    return get_or_create_hcp(db, hcp_name)


def _normalize_interaction_payload(data: dict[str, Any], partial: bool = False) -> dict[str, Any]:
    payload = dict(data)
    normalized: dict[str, Any] = {}
    for field in INTERACTION_FIELDS | {"hcp_id", "hcp_name"}:
        if field in payload and (payload[field] is not None or partial):
            normalized[field] = _normalize_field(field, payload[field])
    return normalized


def _normalize_field(field: str, value: Any) -> Any:
    if field in LIST_FIELDS:
        if value is None:
            return []
        if isinstance(value, list):
            return value
        return [item.strip() for item in str(value).split(",") if item.strip()]
    if field == "date" and isinstance(value, str) and value:
        return date.fromisoformat(value)
    if field == "time" and isinstance(value, str) and value:
        return time.fromisoformat(value)
    if isinstance(value, datetime):
        return value.date() if field == "date" else value.time()
    return value
