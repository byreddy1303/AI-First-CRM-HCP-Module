from __future__ import annotations

import re
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from backend.models import Interaction
from backend.services.crm_service import interactions_for_hcp, search_hcps, serialize_interaction
from backend.services.llm import LLMClient
from backend.tools.search_hcp import _parse_hcp_name


def interaction_summarizer_tool(db: Session, state: dict[str, Any], llm: LLMClient) -> dict[str, Any]:
    extracted = state.get("extracted_data") or llm.extract_interaction(state.get("user_input", ""))
    interaction_id = extracted.get("interaction_id") or _parse_interaction_id(state.get("user_input", ""))
    records: list[dict[str, Any]] = []
    hcp_name = extracted.get("hcp_name") or _parse_hcp_name(state.get("user_input", ""))

    if interaction_id:
        interaction = db.execute(
            select(Interaction)
            .options(joinedload(Interaction.hcp))
            .where(Interaction.id == int(interaction_id))
        ).scalar_one_or_none()
        if interaction:
            records = [serialize_interaction(interaction)]
            hcp_name = records[0]["hcp_name"]
    elif hcp_name:
        matches = search_hcps(db, hcp_name)
        if matches:
            hcp = matches[0]
            hcp_name = hcp.name
            records = [serialize_interaction(row) for row in interactions_for_hcp(db, hcp.id)]
    else:
        interactions = db.execute(
            select(Interaction)
            .options(joinedload(Interaction.hcp))
            .order_by(Interaction.created_at.desc())
            .limit(10)
        ).scalars()
        records = [serialize_interaction(row) for row in interactions]

    if not records:
        return {"error": "No interactions found to summarize."}
    return {"hcp_name": hcp_name, "summary": llm.summarize(records), "source_count": len(records)}


def _parse_interaction_id(text: str) -> int | None:
    match = re.search(r"(?:interaction\s*#?|id\s*#?|#)(\d+)", text, re.IGNORECASE)
    return int(match.group(1)) if match else None

