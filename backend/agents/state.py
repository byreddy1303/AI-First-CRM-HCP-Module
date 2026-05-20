from typing import Any, Optional, TypedDict


class CRMState(TypedDict, total=False):
    user_input: str
    context: dict[str, Any]
    extracted_data: dict[str, Any]
    interaction_id: Optional[int]
    action: str
    tool_output: dict[str, Any]
    response: str
    error: Optional[str]

