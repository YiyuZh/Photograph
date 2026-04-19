from __future__ import annotations

from sqlalchemy import Boolean, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base
from app.models.base import TimestampMixin


class Package(TimestampMixin, Base):
    __tablename__ = "packages"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    task_id: Mapped[int] = mapped_column(ForeignKey("tasks.id"), index=True)
    package_uuid: Mapped[str] = mapped_column(String(36), unique=True, index=True)
    package_name: Mapped[str] = mapped_column(String(255))
    package_path: Mapped[str] = mapped_column(String(512))
    zip_path: Mapped[str | None] = mapped_column(String(512), nullable=True)
    manifest_path: Mapped[str] = mapped_column(String(512))
    metadata_path: Mapped[str] = mapped_column(String(512))
    segments_path: Mapped[str | None] = mapped_column(String(512), nullable=True)
    transcript_path: Mapped[str | None] = mapped_column(String(512), nullable=True)
    contact_sheet_path: Mapped[str | None] = mapped_column(String(512), nullable=True)
    audio_path: Mapped[str | None] = mapped_column(String(512), nullable=True)
    video_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    duration_sec: Mapped[float | None] = mapped_column(Float, nullable=True)
    resolution: Mapped[str | None] = mapped_column(String(64), nullable=True)
    fps: Mapped[float | None] = mapped_column(Float, nullable=True)
    bitrate_kbps: Mapped[float | None] = mapped_column(Float, nullable=True)
    frame_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    segment_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    has_transcript: Mapped[bool] = mapped_column(Boolean, default=False)
    package_status: Mapped[str] = mapped_column(String(32), default="uploaded")
    package_size_bytes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    metadata_json: Mapped[str | None] = mapped_column(Text, nullable=True)

    task = relationship("Task", back_populates="packages")
    files = relationship("PackageFile", back_populates="package", cascade="all, delete-orphan")
    segments = relationship("Segment", back_populates="package", cascade="all, delete-orphan")


class PackageFile(Base):
    __tablename__ = "package_files"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    package_id: Mapped[int] = mapped_column(ForeignKey("packages.id"), index=True)
    relative_path: Mapped[str] = mapped_column(String(512))
    file_type: Mapped[str] = mapped_column(String(64))
    size_bytes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[str] = mapped_column(String(64))

    package = relationship("Package", back_populates="files")


class Segment(Base):
    __tablename__ = "segments"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    package_id: Mapped[int] = mapped_column(ForeignKey("packages.id"), index=True)
    segment_index: Mapped[int] = mapped_column(Integer)
    start_sec: Mapped[float | None] = mapped_column(Float, nullable=True)
    end_sec: Mapped[float | None] = mapped_column(Float, nullable=True)
    duration_sec: Mapped[float | None] = mapped_column(Float, nullable=True)
    title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    keyframe_path: Mapped[str | None] = mapped_column(String(512), nullable=True)
    raw_json: Mapped[str | None] = mapped_column(Text, nullable=True)

    package = relationship("Package", back_populates="segments")
