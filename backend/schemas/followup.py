from datetime import date, datetime

from pydantic import BaseModel, ConfigDict


class FollowUpResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    interaction_id: int
    hcp_name: str
    scheduled_date: date
    note: str
    status: str
    created_at: datetime

