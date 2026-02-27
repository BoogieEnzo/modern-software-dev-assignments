from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import ActionItem
from ..schemas import ActionItemCreate, ActionItemRead

router = APIRouter(prefix="/action-items", tags=["action_items"])


@router.get("/", response_model=list[ActionItemRead])
def list_items(
    completed: Optional[bool] = None, db: Session = Depends(get_db)
) -> list[ActionItemRead]:
    query = select(ActionItem)
    if completed is not None:
        query = query.where(ActionItem.completed.is_(completed))
    rows = db.execute(query).scalars().all()
    return [ActionItemRead.model_validate(row) for row in rows]


@router.post("/", response_model=ActionItemRead, status_code=201)
def create_item(payload: ActionItemCreate, db: Session = Depends(get_db)) -> ActionItemRead:
    item = ActionItem(description=payload.description, completed=False)
    db.add(item)
    db.flush()
    db.refresh(item)
    return ActionItemRead.model_validate(item)


@router.put("/{item_id}/complete", response_model=ActionItemRead)
def complete_item(item_id: int, db: Session = Depends(get_db)) -> ActionItemRead:
    item = db.get(ActionItem, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Action item not found")
    item.completed = True
    db.add(item)
    db.flush()
    db.refresh(item)
    return ActionItemRead.model_validate(item)


@router.post("/bulk-complete", response_model=list[ActionItemRead])
def bulk_complete_items(
    item_ids: list[int], db: Session = Depends(get_db)
) -> list[ActionItemRead]:
    if not item_ids:
        return []

    unique_ids = set(item_ids)
    rows = (
        db.execute(select(ActionItem).where(ActionItem.id.in_(unique_ids)))
        .scalars()
        .all()
    )

    if len(rows) != len(unique_ids):
        raise HTTPException(
            status_code=400, detail="One or more action items not found"
        )

    for item in rows:
        item.completed = True
        db.add(item)

    db.flush()

    return [ActionItemRead.model_validate(row) for row in rows]
