from __future__ import annotations

from fastapi import APIRouter


router = APIRouter(prefix="/api", tags=["system"])


@router.get("/health")
def health():
    return {"success": True, "message": "ok", "data": {"status": "healthy"}}
