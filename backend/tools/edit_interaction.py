from __future__ import annotations

import re
from typing import Any

from sqlalchemy.orm import Session

from backend.services.crm_service import INTERACTION_FIELDS, serialize_interaction, update_interaction
from backend.services.llm import LLMClient


def edit_interaction_tool(db: Session, state: dict[str, Any], llm: LLMClient) -> dict[str, Any]:
    extracted = state.get("extracted_data") or llm.extract_interaction(state.get("user_input", ""))
    interaction_id = extracted.get("interaction_id") or _parse_interaction_id(state.get("user_input", ""))
    updates = _valid_updates(extracted.get("updates") or {})
    if not updates:
        updates = _parse_updates(state.get("user_input", ""))
    if not updates:
        updates = _valid_updates(
            {field: extracted.get(field) for field in ("sentiment", "outcome", "summary") if extracted.get(field)}
        )

    if not interaction_id:
        return {"error": "Tell me which interaction ID to edit, for example interaction #3."}
    if not updates:
        return {"error": "No valid interaction fields were provided for update."}

    interaction = update_interaction(db, int(interaction_id), updates)
    if not interaction:
        return {"error": f"Interaction #{interaction_id} was not found."}

    return {
        "status": "updated",
        "interaction_id": interaction.id,
        "updated_fields": sorted(updates.keys()),
        "record": serialize_interaction(interaction),
    }


def _valid_updates(updates: dict[str, Any]) -> dict[str, Any]:
    return {field: value for field, value in updates.items() if field in INTERACTION_FIELDS and value is not None}


def _parse_interaction_id(text: str) -> int | None:
    match = re.search(r"(?:interaction\s*#?|id\s*#?|#)(\d+)", text, re.IGNORECASE)
    return int(match.group(1)) if match else None


def _parse_updates(text: str) -> dict[str, Any]:
    updates: dict[str, Any] = {}
    sentiment = re.search(r"sentiment\b.{0,30}?\b(positive|neutral|negative)", text, re.IGNORECASE)
    if sentiment:
        updates["sentiment"] = sentiment.group(1).lower()
    outcome = re.search(r"outcome\s+(?:to|as)\s+([^.;]+)", text, re.IGNORECASE)
    if outcome:
        updates["outcome"] = outcome.group(1).strip()
    return updates
