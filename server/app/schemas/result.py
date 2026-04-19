from __future__ import annotations

from pydantic import BaseModel


class ResultCreateRequest(BaseModel):
    content_text: str
    source_model: str | None = None
    source_note: str | None = None
