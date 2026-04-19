from __future__ import annotations

import json
from pathlib import Path

from sqlalchemy.orm import Session

from app.config import get_settings
from app.models import PromptTemplate
from app.services.auth_service import ensure_default_user
from app.services.knowledge_service import load_knowledge_items
from app.services.settings_service import ensure_default_settings


def seed_prompt_templates(db: Session) -> None:
    settings = get_settings()
    template_file = Path(settings.knowledge_root) / "prompt_templates.json"
    if not template_file.exists():
        return
    payload = json.loads(template_file.read_text(encoding="utf-8"))
    for item in payload:
        template = db.query(PromptTemplate).filter(PromptTemplate.template_key == item["template_key"]).one_or_none()
        if template:
            template.task_type = item["task_type"]
            template.name = item["name"]
            template.description = item.get("description")
            template.template_text = item["template_text"]
            template.follow_up_text = item.get("follow_up_text")
            template.fillback_template_text = item.get("fillback_template_text")
            template.is_default = True
            db.add(template)
            continue
        db.add(
            PromptTemplate(
                template_key=item["template_key"],
                task_type=item["task_type"],
                name=item["name"],
                description=item.get("description"),
                template_text=item["template_text"],
                follow_up_text=item.get("follow_up_text"),
                fillback_template_text=item.get("fillback_template_text"),
                is_default=True,
            )
        )
    db.commit()


def initialize_seed_data(db: Session) -> None:
    ensure_default_user(db)
    ensure_default_settings(db)
    seed_prompt_templates(db)
    load_knowledge_items(db)
