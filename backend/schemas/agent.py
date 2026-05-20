from typing import Any, Optional

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str
    context: dict[str, Any] = Field(default_factory=dict)


class ChatResponse(BaseModel):
    action: str
    response: str
    tool_output: dict[str, Any] = Field(default_factory=dict)
    extracted_data: dict[str, Any] = Field(default_factory=dict)
    interaction_id: Optional[int] = None
    error: Optional[str] = None


class ExtractRequest(BaseModel):
    text: str


class ExtractResponse(BaseModel):
    model: str
    extracted_data: dict[str, Any]

