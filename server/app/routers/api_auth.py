from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.deps import get_db, require_user
from app.schemas.auth import LoginRequest
from app.services.auth_service import authenticate_user
from app.routers.serializers import serialize_user


router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/login")
def login(payload: LoginRequest, request: Request, db: Session = Depends(get_db)):
    user = authenticate_user(db, payload.username, payload.password)
    if not user:
        return {"success": False, "message": "用户名或密码错误", "error_code": "AUTH_INVALID_CREDENTIALS", "data": None}
    request.session["user_id"] = user.id
    return {"success": True, "message": "login success", "data": serialize_user(user)}


@router.post("/logout")
def logout(request: Request, user=Depends(require_user)):
    request.session.clear()
    return {"success": True, "message": "logout success", "data": None}


@router.get("/me")
def me(user=Depends(require_user)):
    return {"success": True, "message": "ok", "data": serialize_user(user)}
