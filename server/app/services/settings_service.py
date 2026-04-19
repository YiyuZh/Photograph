from __future__ import annotations

from app.config import get_settings
from app.models import Setting
from app.utils.time import now_iso


DEFAULT_SETTINGS = {
    "storage_root": ("string", "存储根目录", "storage"),
    "max_package_upload_mb": ("int", "最大分析包上传大小（MB）", "150"),
    "default_prompt_template_reference": ("string", "默认拆解模板", "reference_default"),
    "default_prompt_template_improve": ("string", "默认优化模板", "improve_default"),
    "history_keep_days": ("int", "历史保留天数", "365"),
    "public_base_url": ("string", "站点访问地址", "http://127.0.0.1:8000"),
    "timezone": ("string", "默认时区", "Asia/Shanghai"),
}


def ensure_default_settings(db) -> None:
    settings = get_settings()
    DEFAULT_SETTINGS["storage_root"] = ("string", "存储根目录", settings.storage_root.as_posix())
    DEFAULT_SETTINGS["max_package_upload_mb"] = ("int", "最大分析包上传大小（MB）", str(settings.max_package_upload_mb))
    DEFAULT_SETTINGS["default_prompt_template_reference"] = (
        "string",
        "默认拆解模板",
        settings.default_reference_template,
    )
    DEFAULT_SETTINGS["default_prompt_template_improve"] = (
        "string",
        "默认优化模板",
        settings.default_improve_template,
    )
    DEFAULT_SETTINGS["public_base_url"] = ("string", "站点访问地址", settings.app_base_url)

    for key, (value_type, description, value) in DEFAULT_SETTINGS.items():
        existing = db.query(Setting).filter(Setting.setting_key == key).one_or_none()
        if existing:
            continue
        db.add(
            Setting(
                setting_key=key,
                setting_value=value,
                value_type=value_type,
                description=description,
                updated_at=now_iso(),
            )
        )
    db.commit()


def list_settings(db) -> list[Setting]:
    return db.query(Setting).order_by(Setting.setting_key.asc()).all()


def get_settings_map(db) -> dict[str, str]:
    return {item.setting_key: item.setting_value for item in list_settings(db)}


def update_settings(db, updates: dict[str, str]) -> list[Setting]:
    for key, value in updates.items():
        item = db.query(Setting).filter(Setting.setting_key == key).one_or_none()
        if not item:
            continue
        item.setting_value = value
        item.updated_at = now_iso()
        db.add(item)
    db.commit()
    return list_settings(db)
