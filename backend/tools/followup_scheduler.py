from __future__ import annotations

from datetime import date
from typing import Any

from sqlalchemy.orm import Session

from backend.services.crm_service import (
    create_followup,
    interactions_for_hcp,
    search_hcps,
    serialize_followup,
    serialize_interaction,
)
from backend.services.llm import LLMClient
from backend.tools.search_hcp import _parse_hcp_name


def followup_scheduler_tool(db: Session, state: dict[str, Any], llm: LLMClient) -> dict[str, Any]:
    extracted = state.get("extracted_data") or llm.extract_interaction(state.get("user_input", ""))
    query = extracted.get("hcp_name") or _parse_hcp_name(state.get("user_input", ""))
    if not query:
        return {"error": "Tell me which HCP needs a follow-up."}

    matches = search_hcps(db, query)
    if not matches:
        return {"error": f"No HCP found for '{query}'. Log an interaction first."}

    hcp = matches[0]
    interactions = interactions_for_hcp(db, hcp.id)
    if not interactions:
        return {"error": f"No interactions found for {hcp.name}."}

    serialized = [serialize_interaction(row) for row in interactions]
    recommendation = llm.recommend_followup(hcp.name, serialized)
    scheduled_date = date.fromisoformat(recommendation["scheduled_date"])
    followup = create_followup(db, interactions[0].id, scheduled_date, recommendation["note"])
    record = serialize_followup(followup)
    return {
        "status": "scheduled",
        "hcp_id": hcp.id,
        "hcp_name": hcp.name,
        "scheduled_date": record["scheduled_date"],
        "note": record["note"],
        "followup": record,
    }

