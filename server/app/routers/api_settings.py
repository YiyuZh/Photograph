from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.deps import get_db, require_user
from app.models import User
from app.routers.serializers import serialize_setting
from app.schemas.settings import SettingsUpdateRequest
from app.services.settings_service import list_settings, update_settings


router = APIRouter(prefix="/api/settings", tags=["settings"])


@router.get("")
def get_settings_api(db: Session = Depends(get_db), user: User = Depends(require_user)):
    settings = list_settings(db)
    return {"success": True, "message": "ok", "data": [serialize_setting(item) for item in settings]}


@router.patch("")
def patch_settings_api(payload: SettingsUpdateRequest, db: Session = Depends(get_db), user: User = Depends(require_user)):
    settings = update_settings(db, payload.updates)
    return {"success": True, "message": "updated", "data": [serialize_setting(item) for item in settings]}
