from __future__ import annotations

import json
from pathlib import Path
import re

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models import KnowledgeItem


def load_knowledge_items(db: Session) -> None:
    settings = get_settings()
    knowledge_file = Path(settings.knowledge_root) / "items.json"
    if not knowledge_file.exists():
        items: list[dict] = []
    else:
        items = json.loads(knowledge_file.read_text(encoding="utf-8"))
        for item in items:
            item["source_path"] = knowledge_file.name
    items.extend(_load_markdown_items(Path(settings.knowledge_root)))
    for item in items:
        _upsert_knowledge_item(db, item, item.get("source_path"))
    db.commit()


def _upsert_knowledge_item(db: Session, item: dict, source_path: str | None) -> None:
    existing = db.query(KnowledgeItem).filter(KnowledgeItem.item_key == item["item_key"]).one_or_none()
    content_markdown = item["content_markdown"]
    content_text = _markdown_to_text(content_markdown)
    if existing:
        existing.title = item["title"]
        existing.category = item["category"]
        existing.tags = ",".join(item.get("tags", []))
        existing.content_markdown = content_markdown
        existing.content_text = content_text
        existing.source_path = source_path
        db.add(existing)
        return
    db.add(
        KnowledgeItem(
            item_key=item["item_key"],
            title=item["title"],
            category=item["category"],
            tags=",".join(item.get("tags", [])),
            content_markdown=content_markdown,
            content_text=content_text,
            source_path=source_path,
        )
    )


def _load_markdown_items(knowledge_root: Path) -> list[dict]:
    markdown_items: list[dict] = []
    for markdown_path in sorted(knowledge_root.rglob("*.md")):
        if markdown_path.name.upper() == "README.md":
            continue
        if markdown_path.parent == knowledge_root:
            category = "general"
        else:
            category = markdown_path.parent.name
        content = markdown_path.read_text(encoding="utf-8").strip()
        if not content:
            continue
        first_heading = next((line.lstrip("#").strip() for line in content.splitlines() if line.startswith("#")), markdown_path.stem)
        markdown_items.append(
            {
                "item_key": markdown_path.relative_to(knowledge_root).with_suffix("").as_posix().replace("/", "_"),
                "title": first_heading,
                "category": category,
                "tags": [category],
                "content_markdown": content,
                "source_path": markdown_path.relative_to(knowledge_root).as_posix(),
            }
        )
    return markdown_items


def _markdown_to_text(content: str) -> str:
    stripped = re.sub(r"^#+\s*", "", content, flags=re.MULTILINE)
    stripped = re.sub(r"`([^`]*)`", r"\1", stripped)
    stripped = re.sub(r"\[(.*?)\]\((.*?)\)", r"\1", stripped)
    stripped = re.sub(r"[*_>-]", " ", stripped)
    return re.sub(r"\s+", " ", stripped).strip()


def list_knowledge_items(db: Session, category: str | None = None, query: str | None = None) -> list[KnowledgeItem]:
    statement = db.query(KnowledgeItem)
    if category:
        statement = statement.filter(KnowledgeItem.category == category)
    if query:
        like_value = f"%{query}%"
        statement = statement.filter(
            or_(
                KnowledgeItem.title.ilike(like_value),
                KnowledgeItem.content_text.ilike(like_value),
                KnowledgeItem.tags.ilike(like_value),
            )
        )
    return statement.order_by(KnowledgeItem.category.asc(), KnowledgeItem.title.asc()).all()


def get_knowledge_item(db: Session, item_id: int) -> KnowledgeItem | None:
    return db.get(KnowledgeItem, item_id)


def get_related_knowledge(db: Session, task_type: str, keywords: list[str]) -> list[KnowledgeItem]:
    items = list_knowledge_items(db, category=task_type)
    if not keywords:
        return items[:3]
    matched: list[KnowledgeItem] = []
    for item in items:
        haystack = f"{item.title} {item.tags or ''} {item.content_text}".lower()
        if any(keyword.lower() in haystack for keyword in keywords):
            matched.append(item)
    return (matched or items)[:3]
