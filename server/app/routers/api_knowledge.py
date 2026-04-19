from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.deps import get_db, require_user
from app.models import User
from app.routers.serializers import serialize_knowledge_item
from app.services.knowledge_service import get_knowledge_item, list_knowledge_items


router = APIRouter(prefix="/api/knowledge-items", tags=["knowledge"])


@router.get("/search")
def search_knowledge_api(q: str, category: str | None = None, db: Session = Depends(get_db), user: User = Depends(require_user)):
    items = list_knowledge_items(db, category=category, query=q)
    return {"success": True, "message": "ok", "data": [serialize_knowledge_item(item) for item in items]}


@router.get("")
def list_knowledge_api(category: str | None = None, q: str | None = None, db: Session = Depends(get_db), user: User = Depends(require_user)):
    items = list_knowledge_items(db, category=category, query=q)
    return {"success": True, "message": "ok", "data": [serialize_knowledge_item(item) for item in items]}


@router.get("/{item_id}")
def get_knowledge_api(item_id: int, db: Session = Depends(get_db), user: User = Depends(require_user)):
    item = get_knowledge_item(db, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="KNOWLEDGE_NOT_FOUND")
    return {"success": True, "message": "ok", "data": serialize_knowledge_item(item)}
