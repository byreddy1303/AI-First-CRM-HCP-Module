from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from backend.services.crm_service import delete_all_interactions, delete_interaction


def delete_interaction_tool(db: Session, state: dict[str, Any], llm: Any) -> dict[str, Any]:
    extracted = state.get("extracted_data") or {}
    interaction_id = extracted.get("interaction_id") or state.get("interaction_id")
    delete_all = extracted.get("delete_all", False)

    if not interaction_id and not delete_all:
        user_input = (state.get("user_input") or "").lower()
        delete_all = any(phrase in user_input for phrase in ("all", "every", "everything", "clear all"))

    if delete_all:
        count = delete_all_interactions(db)
        return {"deleted_all": True, "count": count}

    if not interaction_id:
        return {"error": "No interaction ID specified. Please provide an ID or say 'delete all'."}

    success = delete_interaction(db, int(interaction_id))
    if not success:
        return {"error": f"Interaction #{interaction_id} not found."}
    return {"interaction_id": interaction_id, "deleted": True}
