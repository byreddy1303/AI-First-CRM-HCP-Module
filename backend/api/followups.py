from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.schemas.followup import FollowUpResponse
from backend.services.crm_service import list_followups, serialize_followup

router = APIRouter(prefix="/api/followups", tags=["followups"])


@router.get("", response_model=list[FollowUpResponse])
def list_followups_route(db: Session = Depends(get_db)):
    return [serialize_followup(row) for row in list_followups(db)]

