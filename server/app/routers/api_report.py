from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.deps import get_db, require_user
from app.models import Report, User
from app.routers.serializers import serialize_report
from app.services.report_service import generate_report, get_current_report, list_reports, set_current_report
from app.services.task_service import get_task


router = APIRouter(tags=["reports"])


@router.post("/api/tasks/{task_id}/report")
def create_report_api(task_id: int, db: Session = Depends(get_db), user: User = Depends(require_user)):
    task = get_task(db, task_id, user.id)
    if not task:
        raise HTTPException(status_code=404, detail="TASK_NOT_FOUND")
    report = generate_report(db, task)
    return {"success": True, "message": "created", "data": serialize_report(report)}


@router.get("/api/tasks/{task_id}/report/current")
def current_report_api(task_id: int, db: Session = Depends(get_db), user: User = Depends(require_user)):
    task = get_task(db, task_id, user.id)
    if not task:
        raise HTTPException(status_code=404, detail="TASK_NOT_FOUND")
    report = get_current_report(task)
    if not report:
        raise HTTPException(status_code=404, detail="REPORT_NOT_FOUND")
    return {"success": True, "message": "ok", "data": serialize_report(report)}


@router.get("/api/tasks/{task_id}/reports")
def list_reports_api(task_id: int, db: Session = Depends(get_db), user: User = Depends(require_user)):
    task = get_task(db, task_id, user.id)
    if not task:
        raise HTTPException(status_code=404, detail="TASK_NOT_FOUND")
    return {"success": True, "message": "ok", "data": [serialize_report(item) for item in list_reports(task)]}


@router.get("/api/reports/{report_id}")
def get_report_api(report_id: int, db: Session = Depends(get_db), user: User = Depends(require_user)):
    report = db.get(Report, report_id)
    if not report or report.task.user_id != user.id:
        raise HTTPException(status_code=404, detail="REPORT_NOT_FOUND")
    return {"success": True, "message": "ok", "data": serialize_report(report)}


@router.post("/api/tasks/{task_id}/reports/{report_id}/set-current")
def set_current_report_api(task_id: int, report_id: int, db: Session = Depends(get_db), user: User = Depends(require_user)):
    task = get_task(db, task_id, user.id)
    if not task:
        raise HTTPException(status_code=404, detail="TASK_NOT_FOUND")
    report = set_current_report(db, task, report_id)
    return {"success": True, "message": "updated", "data": serialize_report(report)}
