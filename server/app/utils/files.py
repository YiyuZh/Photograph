from __future__ import annotations

import json
import shutil
import zipfile
from pathlib import Path


def ensure_relative_to(base: Path, candidate: Path) -> None:
    base_resolved = base.resolve()
    candidate_resolved = candidate.resolve()
    if not str(candidate_resolved).startswith(str(base_resolved)):
        raise ValueError("非法路径")


def safe_extract_zip(zip_path: Path, target_dir: Path) -> list[Path]:
    extracted_files: list[Path] = []
    with zipfile.ZipFile(zip_path) as archive:
        for member in archive.infolist():
            member_path = target_dir / member.filename
            ensure_relative_to(target_dir, member_path)
            if member.is_dir():
                member_path.mkdir(parents=True, exist_ok=True)
                continue
            member_path.parent.mkdir(parents=True, exist_ok=True)
            with archive.open(member) as source, member_path.open("wb") as destination:
                shutil.copyfileobj(source, destination)
            extracted_files.append(member_path)
    return extracted_files


def read_json_file(file_path: Path) -> dict | list:
    with file_path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_text_file(file_path: Path, content: str) -> None:
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text(content, encoding="utf-8")


def relative_to_root(file_path: Path, root: Path) -> str:
    ensure_relative_to(root, file_path)
    return file_path.resolve().relative_to(root.resolve()).as_posix()


def guess_file_type(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix == ".json":
        return "json"
    if suffix in {".jpg", ".jpeg", ".png", ".webp"}:
        return "image"
    if suffix in {".txt", ".md"}:
        return "text"
    if suffix in {".wav", ".mp3", ".m4a"}:
        return "audio"
    if suffix in {".zip"}:
        return "archive"
    return "file"
