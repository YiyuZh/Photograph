from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy.orm import Session

from app.models import Task


def create_task(db: Session, user_id: int, task_type: str, title: str, description: str | None = None) -> Task:
    task = Task(
        task_uuid=str(uuid4()),
        user_id=user_id,
        task_type=task_type,
        title=title,
        description=description,
        status="created",
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


def list_tasks(
    db: Session,
    user_id: int,
    task_type: str | None = None,
    status: str | None = None,
    include_deleted: bool = False,
) -> list[Task]:
    query = db.query(Task).filter(Task.user_id == user_id)
    if not include_deleted:
        query = query.filter(Task.deleted_at.is_(None))
    if task_type:
        query = query.filter(Task.task_type == task_type)
    if status:
        query = query.filter(Task.status == status)
    return query.order_by(Task.created_at.desc()).all()


def get_task(db: Session, task_id: int, user_id: int) -> Task | None:
    return (
        db.query(Task)
        .filter(Task.id == task_id, Task.user_id == user_id, Task.deleted_at.is_(None))
        .one_or_none()
    )


def update_task(task: Task, title: str | None = None, description: str | None = None, status: str | None = None) -> Task:
    if title is not None:
        task.title = title
    if description is not None:
        task.description = description
    if status is not None:
        task.status = status
    return task


def delete_task(db: Session, task: Task) -> Task:
    task.deleted_at = datetime.now(timezone.utc)
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


def recent_reports(db: Session, user_id: int, limit: int = 5):
    from app.models import Report

    return (
        db.query(Report)
        .join(Task, Task.id == Report.task_id)
        .filter(Task.user_id == user_id, Task.deleted_at.is_(None))
        .order_by(Report.created_at.desc())
        .limit(limit)
        .all()
    )
