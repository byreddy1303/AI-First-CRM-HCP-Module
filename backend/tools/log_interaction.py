from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from backend.services.crm_service import create_interaction, serialize_interaction
from backend.services.llm import LLMClient


def log_interaction_tool(db: Session, state: dict[str, Any], llm: LLMClient) -> dict[str, Any]:
    extracted = dict(state.get("extracted_data") or {})
    form_data = state.get("context", {}).get("form_data") or {}
    payload = {**extracted, **form_data}
    if not payload.get("hcp_name") and state.get("user_input"):
        payload.update(llm.extract_interaction(state["user_input"]))
    if not payload.get("summary") and state.get("user_input"):
        payload["summary"] = state["user_input"]

    if not payload.get("hcp_name"):
        return {"error": "I couldn't identify an HCP name. Please include the doctor's name (e.g. 'Met Dr. Smith today…')."}

    interaction = create_interaction(db, payload)
    record = serialize_interaction(interaction)
    return {
        "status": "saved",
        "interaction_id": interaction.id,
        "hcp_name": record["hcp_name"],
        "extracted_data": payload,
        "record": record,
    }

