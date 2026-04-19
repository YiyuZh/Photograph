from __future__ import annotations

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.deps import get_db, require_user
from app.models import User
from app.routers.serializers import serialize_result
from app.schemas.result import ResultCreateRequest
from app.services.result_service import get_current_result, list_results, save_result_text, save_result_upload, set_current_result
from app.services.task_service import get_task


router = APIRouter(tags=["results"])


@router.post("/api/tasks/{task_id}/results")
def create_result_api(
    task_id: int,
    payload: ResultCreateRequest,
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
):
    task = get_task(db, task_id, user.id)
    if not task:
        raise HTTPException(status_code=404, detail="TASK_NOT_FOUND")
    result = save_result_text(db, task, payload.content_text, payload.source_model, payload.source_note)
    return {"success": True, "message": "created", "data": serialize_result(result)}


@router.post("/api/tasks/{task_id}/results/upload")
def upload_result_api(
    task_id: int,
    result_file: UploadFile = File(...),
    source_model: str | None = Form(None),
    source_note: str | None = Form(None),
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
):
    task = get_task(db, task_id, user.id)
    if not task:
        raise HTTPException(status_code=404, detail="TASK_NOT_FOUND")
    result = save_result_upload(db, task, result_file, source_model, source_note)
    return {"success": True, "message": "created", "data": serialize_result(result)}


@router.get("/api/tasks/{task_id}/results/current")
def get_current_result_api(task_id: int, db: Session = Depends(get_db), user: User = Depends(require_user)):
    task = get_task(db, task_id, user.id)
    if not task:
        raise HTTPException(status_code=404, detail="TASK_NOT_FOUND")
    result = get_current_result(task)
    if not result:
        raise HTTPException(status_code=404, detail="RESULT_NOT_FOUND")
    return {"success": True, "message": "ok", "data": serialize_result(result)}


@router.get("/api/tasks/{task_id}/results")
def list_results_api(task_id: int, db: Session = Depends(get_db), user: User = Depends(require_user)):
    task = get_task(db, task_id, user.id)
    if not task:
        raise HTTPException(status_code=404, detail="TASK_NOT_FOUND")
    return {"success": True, "message": "ok", "data": [serialize_result(item) for item in list_results(task)]}


@router.post("/api/tasks/{task_id}/results/{result_id}/set-current")
def set_current_result_api(task_id: int, result_id: int, db: Session = Depends(get_db), user: User = Depends(require_user)):
    task = get_task(db, task_id, user.id)
    if not task:
        raise HTTPException(status_code=404, detail="TASK_NOT_FOUND")
    result = set_current_result(db, task, result_id)
    return {"success": True, "message": "updated", "data": serialize_result(result)}
