from backend.tools.delete_interaction import delete_interaction_tool
from backend.tools.edit_interaction import edit_interaction_tool
from backend.tools.followup_scheduler import followup_scheduler_tool
from backend.tools.log_interaction import log_interaction_tool
from backend.tools.search_hcp import search_hcp_tool
from backend.tools.summarizer import interaction_summarizer_tool

TOOL_REGISTRY = {
    "log": log_interaction_tool,
    "edit": edit_interaction_tool,
    "delete": delete_interaction_tool,
    "search": search_hcp_tool,
    "followup": followup_scheduler_tool,
    "summarize": interaction_summarizer_tool,
}

__all__ = ["TOOL_REGISTRY"]

