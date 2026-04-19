from __future__ import annotations

from pathlib import Path

from fastapi import HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models import Result, Task
from app.utils.files import relative_to_root, write_text_file


def list_results(task: Task) -> list[Result]:
    return sorted(task.results, key=lambda item: item.id, reverse=True)


def get_current_result(task: Task) -> Result | None:
    current_results = [result for result in task.results if result.is_current]
    if current_results:
        return max(current_results, key=lambda item: item.id)
    results = list_results(task)
    return results[0] if results else None


def save_result_text(
    db: Session,
    task: Task,
    content_text: str,
    source_model: str | None,
    source_note: str | None = None,
    source_type: str = "paste",
    filename_suffix: str = ".md",
) -> Result:
    content_text = content_text.strip()
    if not content_text:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="RESULT_EMPTY_CONTENT")

    settings = get_settings()
    version = max((item.id for item in task.results), default=0) + 1
    result_dir = settings.tasks_dir / task.task_uuid / "results"
    result_path = result_dir / f"result_v{version}{filename_suffix}"
    write_text_file(result_path, content_text)

    for existing in task.results:
        existing.is_current = False
        db.add(existing)

    result = Result(
        task_id=task.id,
        source_type=source_type,
        source_model=source_model,
        source_note=source_note,
        content_text=content_text,
        content_path=relative_to_root(result_path, settings.storage_root),
        is_current=True,
    )
    task.status = "result_filled"
    db.add(result)
    db.add(task)
    db.commit()
    db.refresh(result)
    return result


def save_result_upload(
    db: Session,
    task: Task,
    upload: UploadFile,
    source_model: str | None,
    source_note: str | None = None,
) -> Result:
    filename = upload.filename or "result.md"
    suffix = Path(filename).suffix.lower()
    if suffix not in {".txt", ".md"}:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="RESULT_UPLOAD_FAILED")
    content = upload.file.read().decode("utf-8", errors="ignore")
    return save_result_text(
        db,
        task,
        content,
        source_model=source_model,
        source_note=source_note,
        source_type="upload",
        filename_suffix=suffix,
    )


def set_current_result(db: Session, task: Task, result_id: int) -> Result:
    target = next((result for result in task.results if result.id == result_id), None)
    if not target:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="RESULT_NOT_FOUND")
    for existing in task.results:
        existing.is_current = existing.id == result_id
        db.add(existing)
    db.commit()
    db.refresh(target)
    return target
