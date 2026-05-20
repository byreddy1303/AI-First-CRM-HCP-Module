from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class HCPResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    specialty: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    created_at: datetime

