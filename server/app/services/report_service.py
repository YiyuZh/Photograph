from __future__ import annotations

import json

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models import Report, Result, Task
from app.services.result_service import get_current_result
from app.utils.files import relative_to_root, write_text_file


REFERENCE_SECTIONS = [
    "总体结论",
    "风格标签",
    "调色推测",
    "剪辑结构分析",
    "片段拆解",
    "疑似 AI 生成片段提示",
    "仿拍方案",
]

IMPROVE_SECTIONS = [
    "总体判断",
    "必须改",
    "建议改",
    "可选优化",
    "调色建议",
    "剪辑建议",
    "风格提升建议",
]


def list_reports(task: Task) -> list[Report]:
    return sorted(task.reports, key=lambda item: item.version, reverse=True)


def get_current_report(task: Task) -> Report | None:
    current_reports = [report for report in task.reports if report.is_current]
    if current_reports:
        return max(current_reports, key=lambda item: item.version)
    reports = list_reports(task)
    return reports[0] if reports else None


def set_current_report(db: Session, task: Task, report_id: int) -> Report:
    target = next((report for report in task.reports if report.id == report_id), None)
    if not target:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="REPORT_NOT_FOUND")
    for report in task.reports:
        report.is_current = report.id == report_id
        db.add(report)
    db.commit()
    db.refresh(target)
    return target


def _extract_sections(content: str, titles: list[str]) -> dict[str, str]:
    lines = content.splitlines()
    extracted = {title: "" for title in titles}
    current_title: str | None = None
    for raw_line in lines:
        line = raw_line.strip()
        normalized = line.lstrip("#").strip(" ：:")
        matched = next((title for title in titles if normalized == title), None)
        if matched:
            current_title = matched
            continue
        if current_title and line:
            extracted[current_title] = (extracted[current_title] + "\n" + line).strip()
    return extracted


def _extract_summary(content: str) -> str:
    for block in content.split("\n\n"):
        text = block.strip().replace("#", "").strip()
        if text:
            return text[:280]
    return content.strip()[:280]


def generate_report(db: Session, task: Task) -> Report:
    result = get_current_result(task)
    if not result:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="RESULT_NOT_FOUND")

    section_titles = REFERENCE_SECTIONS if task.task_type == "reference" else IMPROVE_SECTIONS
    extracted = _extract_sections(result.content_text, section_titles)
    structured = {
        "task_type": task.task_type,
        "summary": _extract_summary(result.content_text),
        "sections": [{"title": title, "content": extracted.get(title) or "未从原文中提取到该结构，保留原文供人工判断。"} for title in section_titles],
        "raw_content": result.content_text,
    }

    version = max((item.version for item in task.reports), default=0) + 1
    settings = get_settings()
    report_dir = settings.tasks_dir / task.task_uuid / "reports"
    markdown_path = report_dir / f"report_v{version}.md"
    txt_path = report_dir / f"report_v{version}.txt"

    markdown_lines = [
        f"# {task.title} 报告",
        "",
        f"## {section_titles[0]}",
        structured["summary"],
        "",
    ]
    for section in structured["sections"]:
        markdown_lines.extend([f"## {section['title']}", section["content"], ""])
    markdown_lines.extend(["## 原始分析内容", result.content_text.strip(), ""])
    markdown_content = "\n".join(markdown_lines)

    write_text_file(markdown_path, markdown_content)
    write_text_file(txt_path, markdown_content.replace("# ", "").replace("## ", ""))

    for existing in task.reports:
        existing.is_current = False
        db.add(existing)

    report = Report(
        task_id=task.id,
        result_id=result.id,
        version=version,
        title=f"{task.title} 报告 V{version}",
        summary=structured["summary"],
        structured_content=json.dumps(structured, ensure_ascii=False, indent=2),
        markdown_path=relative_to_root(markdown_path, settings.storage_root),
        txt_path=relative_to_root(txt_path, settings.storage_root),
        is_current=True,
    )
    task.status = "report_ready"
    db.add(report)
    db.add(task)
    db.commit()
    db.refresh(report)
    return report
