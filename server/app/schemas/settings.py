from __future__ import annotations

from pydantic import BaseModel


class SettingsUpdateRequest(BaseModel):
    updates: dict[str, str]
