from __future__ import annotations

import json

from markdown import markdown

from app.config import get_settings
from app.models import KnowledgeItem, Package, PackageFile, Prompt, PromptTemplate, Report, Result, Segment, Setting, Task, User
from app.services.package_service import package_summary


def serialize_user(user: User) -> dict:
    return {
        "id": user.id,
        "username": user.username,
        "display_name": user.display_name,
        "last_login_at": user.last_login_at.isoformat() if user.last_login_at else None,
    }


def serialize_task(task: Task) -> dict:
    return {
        "id": task.id,
        "task_uuid": task.task_uuid,
        "task_type": task.task_type,
        "title": task.title,
        "description": task.description,
        "source_video_name": task.source_video_name,
        "status": task.status,
        "created_at": task.created_at.isoformat() if task.created_at else None,
        "updated_at": task.updated_at.isoformat() if task.updated_at else None,
    }


def serialize_package(package: Package) -> dict:
    return package_summary(package)


def serialize_package_file(item: PackageFile) -> dict:
    return {
        "id": item.id,
        "relative_path": item.relative_path,
        "file_type": item.file_type,
        "size_bytes": item.size_bytes,
    }


def serialize_segment(item: Segment) -> dict:
    return {
        "id": item.id,
        "segment_index": item.segment_index,
        "start_sec": item.start_sec,
        "end_sec": item.end_sec,
        "duration_sec": item.duration_sec,
        "title": item.title,
        "summary": item.summary,
        "keyframe_path": item.keyframe_path,
    }


def serialize_prompt_template(item: PromptTemplate) -> dict:
    return {
        "id": item.id,
        "template_key": item.template_key,
        "task_type": item.task_type,
        "name": item.name,
        "description": item.description,
    }


def serialize_prompt(item: Prompt) -> dict:
    return {
        "id": item.id,
        "version": item.version,
        "prompt_text": item.prompt_text,
        "materials_text": item.materials_text,
        "follow_up_text": item.follow_up_text,
        "fillback_template_text": item.fillback_template_text,
        "is_current": item.is_current,
        "created_at": item.created_at,
        "template_name": item.template.name if item.template else None,
    }


def serialize_result(item: Result) -> dict:
    return {
        "id": item.id,
        "source_type": item.source_type,
        "source_model": item.source_model,
        "source_note": item.source_note,
        "content_text": item.content_text,
        "content_path": item.content_path,
        "is_current": item.is_current,
        "created_at": item.created_at.isoformat() if item.created_at else None,
    }


def serialize_report(item: Report) -> dict:
    structured = json.loads(item.structured_content)
    settings = get_settings()
    return {
        "id": item.id,
        "title": item.title,
        "summary": item.summary,
        "version": item.version,
        "is_current": item.is_current,
        "structured_content": structured,
        "markdown_path": item.markdown_path,
        "txt_path": item.txt_path,
        "markdown_url": f"{settings.app_base_url}/reports/{item.id}/download/markdown",
        "txt_url": f"{settings.app_base_url}/reports/{item.id}/download/txt",
    }


def serialize_knowledge_item(item: KnowledgeItem) -> dict:
    return {
        "id": item.id,
        "item_key": item.item_key,
        "title": item.title,
        "category": item.category,
        "tags": item.tags.split(",") if item.tags else [],
        "content_markdown": item.content_markdown,
        "content_html": markdown(item.content_markdown),
    }


def serialize_setting(item: Setting) -> dict:
    return {
        "id": item.id,
        "setting_key": item.setting_key,
        "setting_value": item.setting_value,
        "value_type": item.value_type,
        "description": item.description,
    }
