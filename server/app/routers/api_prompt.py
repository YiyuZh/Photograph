from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.deps import get_db, require_user
from app.models import User
from app.routers.serializers import serialize_prompt, serialize_prompt_template
from app.services.prompt_service import generate_prompt, get_current_prompt, list_prompt_templates, list_prompts, set_current_prompt
from app.services.task_service import get_task


router = APIRouter(tags=["prompts"])


@router.post("/api/tasks/{task_id}/prompts")
def create_prompt_api(task_id: int, db: Session = Depends(get_db), user: User = Depends(require_user)):
    task = get_task(db, task_id, user.id)
    if not task:
        raise HTTPException(status_code=404, detail="TASK_NOT_FOUND")
    prompt = generate_prompt(db, task)
    return {"success": True, "message": "created", "data": serialize_prompt(prompt)}


@router.get("/api/tasks/{task_id}/prompts/current")
def get_current_prompt_api(task_id: int, db: Session = Depends(get_db), user: User = Depends(require_user)):
    task = get_task(db, task_id, user.id)
    if not task:
        raise HTTPException(status_code=404, detail="TASK_NOT_FOUND")
    prompt = get_current_prompt(task)
    if not prompt:
        raise HTTPException(status_code=404, detail="PROMPT_NOT_FOUND")
    return {"success": True, "message": "ok", "data": serialize_prompt(prompt)}


@router.get("/api/tasks/{task_id}/prompts")
def list_prompts_api(task_id: int, db: Session = Depends(get_db), user: User = Depends(require_user)):
    task = get_task(db, task_id, user.id)
    if not task:
        raise HTTPException(status_code=404, detail="TASK_NOT_FOUND")
    return {"success": True, "message": "ok", "data": [serialize_prompt(item) for item in list_prompts(task)]}


@router.post("/api/tasks/{task_id}/prompts/{prompt_id}/set-current")
def set_current_prompt_api(task_id: int, prompt_id: int, db: Session = Depends(get_db), user: User = Depends(require_user)):
    task = get_task(db, task_id, user.id)
    if not task:
        raise HTTPException(status_code=404, detail="TASK_NOT_FOUND")
    try:
        prompt = set_current_prompt(db, task, prompt_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="PROMPT_NOT_FOUND") from None
    return {"success": True, "message": "updated", "data": serialize_prompt(prompt)}


@router.get("/api/prompt-templates")
def list_prompt_templates_api(db: Session = Depends(get_db), user: User = Depends(require_user)):
    templates = list_prompt_templates(db)
    return {"success": True, "message": "ok", "data": [serialize_prompt_template(item) for item in templates]}
