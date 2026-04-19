from __future__ import annotations

import json
from pathlib import Path

from sqlalchemy.orm import Session

from app.config import get_settings
from app.models import Package, Prompt, PromptTemplate, Task
from app.services.knowledge_service import get_related_knowledge
from app.services.package_service import get_latest_package
from app.services.settings_service import get_settings_map
from app.utils.time import now_iso


class SafeDict(dict):
    def __missing__(self, key):
        return ""


def list_prompt_templates(db: Session) -> list[PromptTemplate]:
    return db.query(PromptTemplate).order_by(PromptTemplate.task_type.asc(), PromptTemplate.name.asc()).all()


def _get_default_template(db: Session, task_type: str) -> PromptTemplate:
    settings_map = get_settings_map(db)
    template_key = (
        settings_map.get("default_prompt_template_reference")
        if task_type == "reference"
        else settings_map.get("default_prompt_template_improve")
    )
    template = db.query(PromptTemplate).filter(PromptTemplate.template_key == template_key).one_or_none()
    if template:
        return template
    return db.query(PromptTemplate).filter(PromptTemplate.task_type == task_type).first()


def _read_transcript_excerpt(package: Package) -> str:
    if not package.transcript_path:
        return "无 transcript。"
    settings = get_settings()
    transcript_path = settings.storage_root / package.transcript_path
    if not transcript_path.exists():
        return "无 transcript。"
    content = transcript_path.read_text(encoding="utf-8", errors="ignore").strip()
    if not content:
        return "无 transcript。"
    return content[:1200]


def _build_metadata_summary(package: Package) -> str:
    metadata = json.loads(package.metadata_json) if package.metadata_json else {}
    lines = [
        f"- 文件名：{package.video_name or metadata.get('file_name', '未知')}",
        f"- 时长：{package.duration_sec or metadata.get('duration_sec', '未知')}",
        f"- 分辨率：{package.resolution or metadata.get('resolution', '未知')}",
        f"- 帧率：{package.fps or metadata.get('fps', '未知')}",
        f"- 关键帧数量：{package.frame_count or metadata.get('frame_count', '未知')}",
        f"- 片段数量：{package.segment_count or metadata.get('segment_count', '未知')}",
    ]
    return "\n".join(lines)


def _build_segments_summary(package: Package) -> str:
    if not package.segments:
        return "无 segments.json，建议根据关键帧和 Contact Sheet 进行整体判断。"
    lines = []
    for segment in sorted(package.segments, key=lambda item: item.segment_index)[:12]:
        lines.append(
            f"- 片段 {segment.segment_index}: {segment.start_sec or 0}s - {segment.end_sec or 0}s | {segment.title or '未命名'} | {segment.summary or '无摘要'}"
        )
    return "\n".join(lines)


def _build_materials_text(package: Package) -> str:
    materials = [
        "建议附带素材：",
        f"- Contact Sheet / 关键预览图：{package.contact_sheet_path or '无'}",
        f"- 关键帧目录：{package.package_path}/frames",
        f"- 片段关键帧目录：{package.package_path}/segment_keyframes",
        f"- Transcript：{'有' if package.has_transcript else '无'}",
    ]
    return "\n".join(materials)


def _build_knowledge_summary(db: Session, task: Task, package: Package) -> str:
    keywords = [task.title]
    if package.video_name:
        keywords.append(package.video_name)
    related = get_related_knowledge(db, task.task_type, keywords)
    if not related:
        return "暂无匹配知识条目。"
    return "\n".join(f"- {item.title}: {item.content_text[:120]}" for item in related)


def list_prompts(task: Task) -> list[Prompt]:
    return sorted(task.prompts, key=lambda item: item.version, reverse=True)


def get_current_prompt(task: Task) -> Prompt | None:
    current_prompts = [prompt for prompt in task.prompts if prompt.is_current]
    if current_prompts:
        return max(current_prompts, key=lambda item: item.version)
    prompts = list_prompts(task)
    return prompts[0] if prompts else None


def set_current_prompt(db: Session, task: Task, prompt_id: int) -> Prompt:
    target = next((prompt for prompt in task.prompts if prompt.id == prompt_id), None)
    if not target:
        raise ValueError("PROMPT_NOT_FOUND")
    for prompt in task.prompts:
        prompt.is_current = prompt.id == prompt_id
        db.add(prompt)
    db.commit()
    db.refresh(target)
    return target


def generate_prompt(db: Session, task: Task) -> Prompt:
    package = get_latest_package(task)
    if not package:
        raise ValueError("请先上传分析包，再生成 Prompt。")
    template = _get_default_template(db, task.task_type)
    if not template:
        raise ValueError("当前任务类型缺少默认模板。")

    context = SafeDict(
        task_title=task.title,
        task_description=task.description or "无补充说明",
        video_name=package.video_name or "未知",
        metadata_summary=_build_metadata_summary(package),
        segments_summary=_build_segments_summary(package),
        transcript_summary=_read_transcript_excerpt(package),
        knowledge_summary=_build_knowledge_summary(db, task, package),
    )
    prompt_text = template.template_text.format_map(context)
    materials_text = _build_materials_text(package)

    for prompt in task.prompts:
        prompt.is_current = False
        db.add(prompt)

    version = max((item.version for item in task.prompts), default=0) + 1
    prompt = Prompt(
        task_id=task.id,
        template_id=template.id,
        version=version,
        prompt_text=prompt_text,
        materials_text=materials_text,
        follow_up_text=template.follow_up_text,
        fillback_template_text=template.fillback_template_text,
        is_current=True,
        created_at=now_iso(),
    )
    task.status = "prompt_generated"
    db.add(prompt)
    db.add(task)
    db.commit()
    db.refresh(prompt)
    return prompt
