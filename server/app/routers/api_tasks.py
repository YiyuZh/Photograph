from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.deps import get_db, require_user
from app.models import User
from app.routers.serializers import serialize_task
from app.schemas.task import TaskCreateRequest, TaskUpdateRequest
from app.services.task_service import create_task, delete_task, get_task, list_tasks, update_task


router = APIRouter(prefix="/api/tasks", tags=["tasks"])


@router.post("")
def create_task_api(payload: TaskCreateRequest, db: Session = Depends(get_db), user: User = Depends(require_user)):
    task = create_task(db, user.id, payload.task_type, payload.title, payload.description)
    return {"success": True, "message": "created", "data": serialize_task(task)}


@router.get("")
def list_tasks_api(
    task_type: str | None = None,
    status: str | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
):
    tasks = list_tasks(db, user.id, task_type=task_type, status=status)
    return {"success": True, "message": "ok", "data": [serialize_task(task) for task in tasks]}


@router.get("/{task_id}")
def get_task_api(task_id: int, db: Session = Depends(get_db), user: User = Depends(require_user)):
    task = get_task(db, task_id, user.id)
    if not task:
        raise HTTPException(status_code=404, detail="TASK_NOT_FOUND")
    return {"success": True, "message": "ok", "data": serialize_task(task)}


@router.patch("/{task_id}")
def patch_task_api(
    task_id: int,
    payload: TaskUpdateRequest,
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
):
    task = get_task(db, task_id, user.id)
    if not task:
        raise HTTPException(status_code=404, detail="TASK_NOT_FOUND")
    update_task(task, title=payload.title, description=payload.description, status=payload.status)
    db.add(task)
    db.commit()
    db.refresh(task)
    return {"success": True, "message": "updated", "data": serialize_task(task)}


@router.delete("/{task_id}")
def delete_task_api(task_id: int, db: Session = Depends(get_db), user: User = Depends(require_user)):
    task = get_task(db, task_id, user.id)
    if not task:
        raise HTTPException(status_code=404, detail="TASK_NOT_FOUND")
    delete_task(db, task)
    return {"success": True, "message": "deleted", "data": {"task_id": task_id}}
