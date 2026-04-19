from __future__ import annotations

import json
from pathlib import Path
import shutil
from uuid import uuid4

from fastapi import HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models import Package, PackageFile, Segment, Task
from app.utils.files import guess_file_type, read_json_file, relative_to_root, safe_extract_zip
from app.utils.time import now_iso


def get_latest_package(task: Task) -> Package | None:
    if not task.packages:
        return None
    return max(task.packages, key=lambda item: item.id)


def _find_first_file(base_dir: Path, patterns: list[str]) -> Path | None:
    for pattern in patterns:
        matches = list(base_dir.rglob(pattern))
        if matches:
            return matches[0]
    return None


def _ensure_required_package_files(package_dir: Path) -> tuple[Path, Path, Path | None]:
    manifest_path = package_dir / "task_manifest.json"
    metadata_path = package_dir / "metadata.json"
    contact_sheet = _find_first_file(package_dir, ["contact_sheet.jpg", "contact_sheet.jpeg", "contact_sheet.png"])
    first_frame = _find_first_file(package_dir / "frames", ["*.jpg", "*.jpeg", "*.png"]) if (package_dir / "frames").exists() else None

    if not manifest_path.exists():
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="PACKAGE_REQUIRED_FILE_MISSING: task_manifest.json")
    if not metadata_path.exists():
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="PACKAGE_REQUIRED_FILE_MISSING: metadata.json")
    if not contact_sheet and not first_frame:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="PACKAGE_REQUIRED_FILE_MISSING: contact_sheet or frame",
        )
    return manifest_path, metadata_path, contact_sheet or first_frame


def _extract_segments(package_record: Package, package_dir: Path, segments_file: Path | None) -> list[Segment]:
    if not segments_file or not segments_file.exists():
        return []
    payload = read_json_file(segments_file)
    segment_items = payload if isinstance(payload, list) else payload.get("segments", [])
    segments: list[Segment] = []
    for index, item in enumerate(segment_items):
        keyframe = item.get("keyframe_path") or item.get("keyframe") or item.get("frame")
        if keyframe:
            keyframe = str(Path(keyframe).as_posix())
        segments.append(
            Segment(
                package_id=package_record.id,
                segment_index=item.get("segment_index", index),
                start_sec=item.get("start_sec") or item.get("start"),
                end_sec=item.get("end_sec") or item.get("end"),
                duration_sec=item.get("duration_sec") or item.get("duration"),
                title=item.get("title") or item.get("label"),
                summary=item.get("summary") or item.get("description"),
                keyframe_path=keyframe,
                raw_json=json.dumps(item, ensure_ascii=False),
            )
        )
    return segments


def _index_package_files(package_record: Package, package_dir: Path) -> list[PackageFile]:
    files: list[PackageFile] = []
    settings = get_settings()
    for file_path in sorted(package_dir.rglob("*")):
        if file_path.is_dir():
            continue
        files.append(
            PackageFile(
                package_id=package_record.id,
                relative_path=relative_to_root(file_path, settings.storage_root),
                file_type=guess_file_type(file_path),
                size_bytes=file_path.stat().st_size,
                created_at=now_iso(),
            )
        )
    return files


def upload_package(db: Session, task: Task, upload: UploadFile) -> Package:
    settings = get_settings()
    filename = upload.filename or "analysis_package.zip"
    if not filename.lower().endswith(".zip"):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="PACKAGE_INVALID_FORMAT")

    max_bytes = settings.max_package_upload_mb * 1024 * 1024
    content = upload.file.read(max_bytes + 1)
    if len(content) > max_bytes:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="PACKAGE_FILE_TOO_LARGE")

    task_root = settings.tasks_dir / task.task_uuid
    upload_dir = task_root / "uploads"
    upload_dir.mkdir(parents=True, exist_ok=True)

    package_uuid = str(uuid4())
    zip_path = upload_dir / f"{package_uuid}.zip"
    zip_path.write_bytes(content)

    package_dir = task_root / "package" / package_uuid
    package_dir.mkdir(parents=True, exist_ok=True)
    try:
        safe_extract_zip(zip_path, package_dir)

        manifest_path, metadata_path, preview_path = _ensure_required_package_files(package_dir)
        metadata = read_json_file(metadata_path)
        manifest = read_json_file(manifest_path)
        segments_path = package_dir / "segments.json"
        transcript_path = package_dir / "transcript.txt"
        audio_path = _find_first_file(package_dir, ["audio.wav", "audio.mp3", "audio.m4a"])

        package_record = Package(
            task_id=task.id,
            package_uuid=package_uuid,
            package_name=manifest.get("package_name") or manifest.get("task_name") or filename,
            package_path=relative_to_root(package_dir, settings.storage_root),
            zip_path=relative_to_root(zip_path, settings.storage_root),
            manifest_path=relative_to_root(manifest_path, settings.storage_root),
            metadata_path=relative_to_root(metadata_path, settings.storage_root),
            segments_path=relative_to_root(segments_path, settings.storage_root) if segments_path.exists() else None,
            transcript_path=relative_to_root(transcript_path, settings.storage_root) if transcript_path.exists() else None,
            contact_sheet_path=relative_to_root(preview_path, settings.storage_root),
            audio_path=relative_to_root(audio_path, settings.storage_root) if audio_path else None,
            video_name=metadata.get("file_name") or metadata.get("video_name") or manifest.get("video_name"),
            duration_sec=metadata.get("duration_sec") or metadata.get("duration"),
            resolution=metadata.get("resolution"),
            fps=metadata.get("fps"),
            bitrate_kbps=metadata.get("bitrate_kbps"),
            frame_count=metadata.get("frame_count"),
            segment_count=metadata.get("segment_count"),
            has_transcript=transcript_path.exists(),
            package_status="parsed",
            package_size_bytes=len(content),
            metadata_json=json.dumps(metadata, ensure_ascii=False, indent=2),
        )
        db.add(package_record)
        db.flush()

        for item in _index_package_files(package_record, package_dir):
            db.add(item)
        for segment in _extract_segments(package_record, package_dir, segments_path if segments_path.exists() else None):
            db.add(segment)

        task.source_video_name = package_record.video_name
        task.status = "package_uploaded"
        db.add(task)
        db.commit()
        db.refresh(package_record)
        return package_record
    except Exception:
        db.rollback()
        if package_dir.exists():
            shutil.rmtree(package_dir, ignore_errors=True)
        if zip_path.exists():
            zip_path.unlink(missing_ok=True)
        raise


def package_summary(package: Package) -> dict:
    metadata = json.loads(package.metadata_json) if package.metadata_json else {}
    return {
        "id": package.id,
        "package_uuid": package.package_uuid,
        "package_name": package.package_name,
        "video_name": package.video_name,
        "duration_sec": package.duration_sec,
        "resolution": package.resolution,
        "fps": package.fps,
        "frame_count": package.frame_count,
        "segment_count": package.segment_count,
        "has_transcript": package.has_transcript,
        "contact_sheet_path": package.contact_sheet_path,
        "metadata": metadata,
    }
