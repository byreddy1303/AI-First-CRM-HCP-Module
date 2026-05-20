from datetime import date as DateType
from datetime import datetime
from datetime import time as TimeType
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field


class InteractionBase(BaseModel):
    hcp_id: Optional[int] = None
    hcp_name: Optional[str] = None
    interaction_type: str = "meeting"
    date: Optional[DateType] = None
    time: Optional[TimeType] = None
    attendees: list[str] = Field(default_factory=list)
    topics: list[str] = Field(default_factory=list)
    materials_shared: list[str] = Field(default_factory=list)
    samples_distributed: list[str] = Field(default_factory=list)
    sentiment: Optional[str] = None
    outcome: Optional[str] = None
    follow_up_actions: list[str] = Field(default_factory=list)
    summary: Optional[str] = None


class InteractionCreate(InteractionBase):
    pass


class InteractionUpdate(BaseModel):
    interaction_type: Optional[str] = None
    date: Optional[DateType] = None
    time: Optional[TimeType] = None
    attendees: Optional[list[str]] = None
    topics: Optional[list[str]] = None
    materials_shared: Optional[list[str]] = None
    samples_distributed: Optional[list[str]] = None
    sentiment: Optional[str] = None
    outcome: Optional[str] = None
    follow_up_actions: Optional[list[str]] = None
    summary: Optional[str] = None


class InteractionResponse(InteractionBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    hcp_id: int
    hcp_name: str
    created_at: datetime
    updated_at: datetime


class InteractionPayload(BaseModel):
    data: dict[str, Any]
