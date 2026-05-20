from __future__ import annotations

import re
from typing import Any

from sqlalchemy.orm import Session

from backend.services.crm_service import interactions_for_hcp, search_hcps, serialize_interaction
from backend.services.llm import LLMClient


def search_hcp_tool(db: Session, state: dict[str, Any], llm: LLMClient) -> dict[str, Any]:
    extracted = state.get("extracted_data") or llm.extract_interaction(state.get("user_input", ""))
    query = extracted.get("hcp_name") or _parse_hcp_name(state.get("user_input", ""))
    if not query:
        return {"error": "Tell me the HCP name to search."}

    matches = search_hcps(db, query)
    if not matches:
        return {"hcp_name": query, "interactions": []}

    hcp = matches[0]
    interactions = [serialize_interaction(row) for row in interactions_for_hcp(db, hcp.id)]
    return {
        "hcp_id": hcp.id,
        "hcp_name": hcp.name,
        "matches": [{"id": row.id, "name": row.name, "specialty": row.specialty} for row in matches],
        "interactions": interactions,
    }


_NAME_STOP_WORDS = frozenset({
    "today", "yesterday", "tomorrow", "about", "for", "with", "and",
    "the", "to", "at", "on", "in", "is", "was", "he", "she", "they",
    "his", "her", "their", "we", "i", "a", "an", "said", "that",
})


def _parse_hcp_name(text: str) -> str | None:
    match = re.search(r"\bDr\.?\s*(\w+)(?:\s+(\w+))?", text, re.IGNORECASE)
    if match:
        parts = [match.group(1)]
        second = match.group(2)
        if second and second.lower() not in _NAME_STOP_WORDS:
            parts.append(second)
        return "Dr. " + " ".join(parts).title()
    with_match = re.search(r"(?:with|for)\s+(\w+(?:\s+\w+)?)", text, re.IGNORECASE)
    return with_match.group(1).title() if with_match else None

