from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import HCP
from backend.schemas.hcp import HCPResponse
from backend.schemas.interaction import InteractionResponse
from backend.services.crm_service import interactions_for_hcp, search_hcps, serialize_interaction

router = APIRouter(prefix="/api/hcp", tags=["hcp"])


@router.get("", response_model=list[HCPResponse])
def search_hcp_route(
    q: str = Query("", description="Partial HCP name to search"),
    db: Session = Depends(get_db),
):
    """Return HCPs matching the name query (used for autocomplete)."""
    from sqlalchemy import select
    if q:
        results = search_hcps(db, q)
    else:
        results = list(db.execute(
            select(HCP).order_by(HCP.name).limit(100)
        ).scalars())
    return results


@router.get("/{hcp_id}/interactions", response_model=list[InteractionResponse])
def hcp_interactions_route(hcp_id: int, db: Session = Depends(get_db)):
    if not db.get(HCP, hcp_id):
        raise HTTPException(status_code=404, detail="HCP not found")
    return [serialize_interaction(row) for row in interactions_for_hcp(db, hcp_id)]
