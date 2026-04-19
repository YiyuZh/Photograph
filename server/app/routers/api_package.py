from __future__ import annotations

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.deps import get_db, require_user
from app.models import User
from app.routers.serializers import serialize_package, serialize_package_file, serialize_segment
from app.services.package_service import get_latest_package, upload_package
from app.services.task_service import get_task


router = APIRouter(prefix="/api/tasks/{task_id}", tags=["packages"])


@router.post("/package")
def upload_package_api(
    task_id: int,
    package_file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
):
    task = get_task(db, task_id, user.id)
    if not task:
        raise HTTPException(status_code=404, detail="TASK_NOT_FOUND")
    package = upload_package(db, task, package_file)
    return {"success": True, "message": "uploaded", "data": serialize_package(package)}


@router.get("/package")
def get_package_api(task_id: int, db: Session = Depends(get_db), user: User = Depends(require_user)):
    task = get_task(db, task_id, user.id)
    if not task:
        raise HTTPException(status_code=404, detail="TASK_NOT_FOUND")
    package = get_latest_package(task)
    if not package:
        raise HTTPException(status_code=404, detail="PACKAGE_NOT_FOUND")
    return {"success": True, "message": "ok", "data": serialize_package(package)}


@router.get("/package/files")
def get_package_files_api(task_id: int, db: Session = Depends(get_db), user: User = Depends(require_user)):
    task = get_task(db, task_id, user.id)
    if not task:
        raise HTTPException(status_code=404, detail="TASK_NOT_FOUND")
    package = get_latest_package(task)
    if not package:
        raise HTTPException(status_code=404, detail="PACKAGE_NOT_FOUND")
    return {"success": True, "message": "ok", "data": [serialize_package_file(item) for item in package.files]}


@router.get("/segments")
def get_segments_api(task_id: int, db: Session = Depends(get_db), user: User = Depends(require_user)):
    task = get_task(db, task_id, user.id)
    if not task:
        raise HTTPException(status_code=404, detail="TASK_NOT_FOUND")
    package = get_latest_package(task)
    if not package:
        raise HTTPException(status_code=404, detail="PACKAGE_NOT_FOUND")
    segments = sorted(package.segments, key=lambda item: item.segment_index)
    return {"success": True, "message": "ok", "data": [serialize_segment(item) for item in segments]}
