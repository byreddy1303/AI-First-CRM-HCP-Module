from __future__ import annotations

import json
import logging
import os
import re
from datetime import date, timedelta
from functools import lru_cache
from typing import Any, Optional


log = logging.getLogger(__name__)

VALID_ACTIONS = {"log", "edit", "delete", "search", "followup", "summarize"}


class LLMClient:
    """Groq client wrapper (gemma2-9b-it) with local regex fallbacks."""

    def __init__(self, model: Optional[str] = None) -> None:
        self.model = model or os.getenv("GROQ_MODEL", "gemma2-9b-it")
        self._client = None
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            log.warning("GROQ_API_KEY not set — using local fallback mode.")
            return
        try:
            from groq import Groq
            self._client = Groq(api_key=api_key)
        except Exception as exc:
            log.warning("Failed to initialise Groq client: %s", exc)

    def classify_intent(self, user_input: str) -> str:
        prompt = (
            "Classify this CRM assistant message as exactly one action: "
            "log, edit, delete, search, followup, summarize. Return JSON: {\"action\":\"...\"}.\n"
            f"Message: {user_input}"
        )
        data = self._chat_json(prompt)
        action = str(data.get("action", "")).lower()
        if action in VALID_ACTIONS:
            return action
        return self._fallback_intent(user_input)

    def extract_interaction(self, user_input: str) -> dict[str, Any]:
        prompt = (
            "Extract CRM interaction entities from the message. Return JSON with keys: "
            "hcp_name, interaction_type, date, time, attendees, topics, materials_shared, "
            "samples_distributed, sentiment, outcome, follow_up_actions, updates, interaction_id. "
            "Use null or [] when unknown.\n"
            f"Message: {user_input}"
        )
        data = self._chat_json(prompt)
        if data:
            return self._clean_extraction(data)
        return self._fallback_extract(user_input)

    def recommend_followup(self, hcp_name: str, interactions: list[dict[str, Any]]) -> dict[str, Any]:
        prompt = (
            "Recommend one CRM follow-up for this HCP. Return JSON with scheduled_date "
            "as YYYY-MM-DD and note.\n"
            f"HCP: {hcp_name}\nInteractions: {json.dumps(interactions, default=str)}"
        )
        data = self._chat_json(prompt)
        if data.get("scheduled_date") and data.get("note"):
            return {"scheduled_date": data["scheduled_date"], "note": data["note"]}
        return {
            "scheduled_date": (date.today() + timedelta(days=7)).isoformat(),
            "note": f"Follow up with {hcp_name} on open outcomes and next clinical discussion points.",
        }

    def summarize(self, interactions: list[dict[str, Any]]) -> str:
        if not interactions:
            return "No interactions found to summarize."
        prompt = (
            "Summarize these HCP CRM interactions in one concise CRM-ready paragraph. "
            "Include themes, sentiment, outcomes, and follow-up needs.\n"
            f"Interactions: {json.dumps(interactions, default=str)}"
        )
        content = self._chat_text(prompt)
        if content:
            return content.strip()
        hcp_name = interactions[0].get("hcp_name", "the HCP")
        topics = sorted({topic for row in interactions for topic in row.get("topics", [])})
        sentiment = interactions[-1].get("sentiment") or "neutral"
        return (
            f"{hcp_name} has {len(interactions)} recorded interaction(s). "
            f"Recent discussions covered {', '.join(topics) if topics else 'general CRM topics'}, "
            f"with latest sentiment marked as {sentiment}."
        )

    def generate_response(self, action: str, tool_output: dict[str, Any]) -> str:
        if tool_output.get("error"):
            return tool_output["error"]
        if action == "log":
            return f"Logged interaction #{tool_output.get('interaction_id')} for {tool_output.get('hcp_name')}."
        if action == "delete":
            if tool_output.get("deleted_all"):
                return f"Deleted all {tool_output.get('count', 0)} interaction(s)."
            return f"Deleted interaction #{tool_output.get('interaction_id')}."
        if action == "edit":
            fields = ", ".join(tool_output.get("updated_fields", []))
            return f"Updated interaction #{tool_output.get('interaction_id')}: {fields}."
        if action == "search":
            count = len(tool_output.get("interactions", []))
            return f"Found {count} interaction(s) for {tool_output.get('hcp_name')}."
        if action == "followup":
            return (
                f"Scheduled follow-up for {tool_output.get('hcp_name')} on "
                f"{tool_output.get('scheduled_date')}: {tool_output.get('note')}"
            )
        if action == "summarize":
            return tool_output.get("summary", "No summary available.")
        return "Request handled."

    # ── private helpers ──────────────────────────────────────────────────────

    def _chat_text(self, prompt: str) -> Optional[str]:
        if not self._client:
            return None
        try:
            response = self._client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an AI-first CRM assistant for HCP field interactions."},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.1,
            )
            return response.choices[0].message.content
        except Exception as exc:
            log.warning("Groq _chat_text failed: %s", exc)
            return None

    def _chat_json(self, prompt: str) -> dict[str, Any]:
        if not self._client:
            return {}
        try:
            response = self._client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "Return valid JSON only. Do not include markdown."},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.1,
                response_format={"type": "json_object"},
            )
            content = response.choices[0].message.content or "{}"
            return json.loads(content)
        except Exception as exc:
            log.warning("Groq _chat_json failed: %s", exc)
            return {}

    def _fallback_intent(self, user_input: str) -> str:
        text = user_input.lower()
        if any(word in text for word in ("delete", "remove", "erase", "clear", "wipe")):
            return "delete"
        if any(word in text for word in ("edit", "change", "update", "correct", "modify")):
            return "edit"
        if any(word in text for word in ("summarize", "summary", "recap", "report")):
            return "summarize"
        if any(word in text for word in ("show", "find", "search", "history", "interactions with")):
            return "search"
        if any(phrase in text for phrase in ("when should", "schedule follow", "next follow", "next step")):
            return "followup"
        if re.search(r"\b(log|record|met|meeting|called|emailed|visited|discussed)\b", text):
            return "log"
        if any(phrase in text for phrase in ("follow up", "follow-up")):
            return "followup"
        # A bare HCP name with no action keywords → treat as a search
        if re.search(r"^dr\.?\s*\w+", text, re.IGNORECASE):
            return "search"
        return "log"

    def _fallback_extract(self, user_input: str) -> dict[str, Any]:
        text = user_input.strip()
        explicit_hcp = re.search(r"\bDr\.?\s*(\w+(?:\s+\w+)?)", text, re.IGNORECASE)
        if explicit_hcp:
            raw = re.sub(r"(?i)^Dr\.?\s*", "", explicit_hcp.group(0)).strip().title()
            hcp_name = f"Dr. {raw}"
        else:
            hcp_name = None
        if not hcp_name:
            hcp_match = re.search(
                r"\b(?:with|for|met|called|emailed|visited)\s+(\w+(?:\s+\w+)?)",
                text,
                re.IGNORECASE,
            )
            hcp_name = hcp_match.group(1).title() if hcp_match else None

        topics: list[str] = []
        topic_match = re.search(r"(?:about|discussed|regarding|on)\s+([^.;]+)", text, re.IGNORECASE)
        if topic_match:
            topic_text = re.split(
                r"\b(?:sentiment|follow up|follow-up|outcome)\b",
                topic_match.group(1),
                flags=re.IGNORECASE,
            )[0]
            topics = [part.strip() for part in re.split(r",| and ", topic_text) if part.strip()]

        materials = [
            item
            for item in ("brochure", "clinical paper", "study", "deck", "sample kit")
            if item in text.lower()
        ]
        samples = ["samples"] if "sample" in text.lower() else []
        sentiment = "neutral"
        if re.search(r"\b(positive|interested|receptive|good|agreed|happy)\b", text, re.IGNORECASE):
            sentiment = "positive"
        elif re.search(r"\b(negative|concern|objection|not interested|poor)\b", text, re.IGNORECASE):
            sentiment = "negative"

        interaction_id = None
        id_match = re.search(r"(?:interaction\s*#?|id\s*#?|#)(\d+)", text, re.IGNORECASE)
        if id_match:
            interaction_id = int(id_match.group(1))

        updates: dict[str, Any] = {}
        sentiment_update = re.search(r"sentiment\s+(?:to|as)\s+(positive|neutral|negative)", text, re.IGNORECASE)
        if sentiment_update:
            updates["sentiment"] = sentiment_update.group(1).lower()

        return self._clean_extraction(
            {
                "hcp_name": hcp_name,
                "interaction_type": "call" if "call" in text.lower() else "meeting",
                "date": date.today().isoformat() if "today" in text.lower() else None,
                "time": None,
                "attendees": [],
                "topics": topics,
                "materials_shared": materials,
                "samples_distributed": samples,
                "sentiment": sentiment,
                "outcome": None,
                "follow_up_actions": ["Follow up"] if "follow" in text.lower() else [],
                "updates": updates,
                "interaction_id": interaction_id,
            }
        )

    def _clean_extraction(self, data: dict[str, Any]) -> dict[str, Any]:
        list_fields = {"attendees", "topics", "materials_shared", "samples_distributed", "follow_up_actions"}
        cleaned = dict(data)
        for field in list_fields:
            value = cleaned.get(field)
            if value is None:
                cleaned[field] = []
            elif isinstance(value, str):
                cleaned[field] = [part.strip() for part in re.split(r",|;", value) if part.strip()]
        updates = cleaned.get("updates")
        cleaned["updates"] = updates if isinstance(updates, dict) else {}
        return cleaned


@lru_cache(maxsize=1)
def get_llm_client() -> LLMClient:
    """Return a module-level singleton LLMClient (used as a FastAPI dependency)."""
    return LLMClient()
