from __future__ import annotations

from sqlalchemy import Boolean, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base
from app.models.base import TimestampMixin


class Result(TimestampMixin, Base):
    __tablename__ = "results"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    task_id: Mapped[int] = mapped_column(ForeignKey("tasks.id"), index=True)
    source_type: Mapped[str] = mapped_column(String(32), default="paste")
    source_model: Mapped[str | None] = mapped_column(String(128), nullable=True)
    source_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    content_text: Mapped[str] = mapped_column(Text)
    content_path: Mapped[str | None] = mapped_column(String(512), nullable=True)
    is_current: Mapped[bool] = mapped_column(Boolean, default=True, index=True)

    task = relationship("Task", back_populates="results")
    reports = relationship("Report", back_populates="result")


class Report(TimestampMixin, Base):
    __tablename__ = "reports"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    task_id: Mapped[int] = mapped_column(ForeignKey("tasks.id"), index=True)
    result_id: Mapped[int | None] = mapped_column(ForeignKey("results.id"), nullable=True)
    version: Mapped[int] = mapped_column(Integer, default=1)
    title: Mapped[str] = mapped_column(String(255))
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    structured_content: Mapped[str] = mapped_column(Text)
    markdown_path: Mapped[str | None] = mapped_column(String(512), nullable=True)
    txt_path: Mapped[str | None] = mapped_column(String(512), nullable=True)
    is_current: Mapped[bool] = mapped_column(Boolean, default=True, index=True)

    task = relationship("Task", back_populates="reports")
    result = relationship("Result", back_populates="reports")
