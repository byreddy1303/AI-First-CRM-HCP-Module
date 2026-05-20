from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.schemas.interaction import InteractionCreate, InteractionResponse, InteractionUpdate
from backend.services.crm_service import (
    create_interaction,
    delete_all_interactions,
    delete_interaction,
    get_interaction,
    list_interactions,
    serialize_interaction,
    update_interaction,
)

router = APIRouter(prefix="/api/interactions", tags=["interactions"])


@router.get("", response_model=list[InteractionResponse])
def list_interactions_route(
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    return [serialize_interaction(row) for row in list_interactions(db, limit=limit)]


@router.post("", response_model=InteractionResponse)
def create_interaction_route(payload: InteractionCreate, db: Session = Depends(get_db)):
    interaction = create_interaction(db, payload.model_dump(exclude_none=True))
    return serialize_interaction(interaction)


@router.get("/{interaction_id}", response_model=InteractionResponse)
def get_interaction_route(interaction_id: int, db: Session = Depends(get_db)):
    interaction = get_interaction(db, interaction_id)
    if not interaction:
        raise HTTPException(status_code=404, detail="Interaction not found")
    return serialize_interaction(interaction)


@router.put("/{interaction_id}", response_model=InteractionResponse)
def update_interaction_route(
    interaction_id: int,
    payload: InteractionUpdate,
    db: Session = Depends(get_db),
):
    interaction = update_interaction(db, interaction_id, payload.model_dump(exclude_none=True))
    if not interaction:
        raise HTTPException(status_code=404, detail="Interaction not found")
    return serialize_interaction(interaction)


@router.delete("", status_code=200)
def delete_all_interactions_route(db: Session = Depends(get_db)):
    count = delete_all_interactions(db)
    return {"deleted": count}


@router.delete("/{interaction_id}", status_code=204)
def delete_interaction_route(interaction_id: int, db: Session = Depends(get_db)):
    deleted = delete_interaction(db, interaction_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Interaction not found")
