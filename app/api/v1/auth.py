import uuid
from datetime import datetime, timezone, timedelta
import base64
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session as OrmSession
from sqlalchemy import select
from app.db.session import get_db
from app.core.config import settings
from app.core.security import verify_password, hash_password
from app.models import user
from app.models.user import User
from app.models.session import Session as SessionModel
from app.models.enums import UserRole, SessionEndReason
from app.schemas.auth import (
LoginIn, LoginSuccessOut, FirstLoginRequiredOut, FirstLoginChangeIn,
RoleInUseOut, RequestResetIn, ResetPasswordIn
)
from app.schemas.common import SessionCheckOut, MessageOut
from app.services.email_service import send_email
from app.services.locks import get_active_lock, acquire_lock, release_lock_if_owner

router = APIRouter()

# Export router for FastAPI include_router usage
__all__ = ["router"]

def _now():
    return datetime.now(timezone.utc)

@router.post("/login", response_model=LoginSuccessOut | FirstLoginRequiredOut | RoleInUseOut)
def login(payload: LoginIn, request: Request, db: OrmSession = Depends(get_db)):
    user = db.execute(select(User).where(User.username == payload.username)).scalar_one_or_none()
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    
    if user.is_first_login:
        return FirstLoginRequiredOut()

# Create session
    session_id = uuid.uuid4().hex
    expires_at = _now() + timedelta(minutes=settings.SESSION_DURATION_MINUTES)
    ip = request.client.host if request.client else None
    ua = request.headers.get("user-agent", "")

    sess = SessionModel(
        session_id=session_id,
        user_id=user.id,
        role=user.role,
        expires_at=expires_at,
        ip_address=ip,
        user_agent=ua,
    )
    db.add(sess)
    db.commit()
    db.refresh(sess)

    # Role lock for OFFICER/SUPERVISOR
    if user.role in (UserRole.OFFICER, UserRole.SUPERVISOR):
        active = get_active_lock(db, user.role)
        if active:
            # Cleanup created session since we can't use it
            sess.logout_at = _now()
            sess.ended_reason = SessionEndReason.EXPIRED
            db.commit()
            return RoleInUseOut(role_in_use=True, locked_since=active.locked_at, message="Role currently in use by another user")
        acquired = acquire_lock(db, user.role, sess)
        if not acquired:
            sess.logout_at = _now()
            sess.ended_reason = SessionEndReason.EXPIRED
            db.commit()
            return RoleInUseOut(role_in_use=True, locked_since=None, message="Role currently in use by another user")

    return LoginSuccessOut(session_id=session_id, role=user.role.value, username=user.username, expires_at=expires_at)

@router.get("/session-check", response_model=SessionCheckOut)
def session_check(x_session_id: str | None = None, db: OrmSession = Depends(get_db)):
    if not x_session_id:
        return SessionCheckOut(valid=False)
    sess = db.execute(select(SessionModel).where(SessionModel.session_id == x_session_id)).scalar_one_or_none()
    if not sess or sess.logout_at is not None:
        return SessionCheckOut(valid=False)
    if sess.expires_at <= _now():
        if sess.logout_at is None:
            sess.logout_at = sess.expires_at
            sess.ended_reason = SessionEndReason.EXPIRED
            db.commit()
        if sess.role in (UserRole.OFFICER, UserRole.SUPERVISOR):
            release_lock_if_owner(db, sess.role, sess)
        return SessionCheckOut(valid=False)
    user = db.get(User, sess.user_id)
    if not user or not user.is_active:
        return SessionCheckOut(valid=False)
    return SessionCheckOut(valid=True, username=user.username, role=user.role.value, expires_at=sess.expires_at)

@router.post("/logout", response_model=MessageOut)
def logout(x_session_id: str | None = None, db: OrmSession = Depends(get_db)):
    if not x_session_id:
        return MessageOut(message="Logged out")
    sess = db.execute(select(SessionModel).where(SessionModel.session_id == x_session_id)).scalar_one_or_none()
    if not sess or sess.logout_at is not None:
        return MessageOut(message="Logged out")
    sess.logout_at = _now()
    sess.ended_reason = SessionEndReason.LOGOUT
    db.commit()
    if sess.role in (UserRole.OFFICER, UserRole.SUPERVISOR):
        release_lock_if_owner(db, sess.role, sess)
    return MessageOut(message="Logged out")

@router.post("/first-login-change", response_model=MessageOut)
def first_login_change(payload: FirstLoginChangeIn, db: OrmSession = Depends(get_db)):
    user = db.execute(select(User).where(User.username == payload.username)).scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if not user.is_first_login:
        raise HTTPException(status_code=403, detail="Already completed first login change")
    if not verify_password(payload.old_password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    if payload.new_password == settings.DEFAULT_PASSWORD:
        raise HTTPException(status_code=400, detail="New password cannot be the default password")
        user.hashed_password = hash_password(payload.new_password)
        user.is_first_login = False
        db.commit()
    return MessageOut(message="Password updated, please log in")

def make_reset_token(email: str) -> str:
    raw = f"{email}:{int(_now().timestamp())}"
    return base64.urlsafe_b64encode(raw.encode()).decode()

def parse_reset_token(token: str) -> str | None:
    try:
        raw = base64.urlsafe_b64decode(token.encode()).decode()
        email, ts = raw.split(":")
        if (_now().timestamp() - int(ts)) > settings.PASSWORD_RESET_TOKEN_EXPIRE_MINUTES * 60:
            return None
        return email
    
    except Exception:
        return None

@router.post("/request-reset", response_model=MessageOut)
def request_reset(payload: RequestResetIn, db: OrmSession = Depends(get_db)):
    user = db.execute(select(User).where(User.email == payload.email)).scalar_one_or_none()
    if not user:
        return MessageOut(message="If this email exists, a reset token was sent")
    token = make_reset_token(user.email)
    send_email(user.email, "Password Reset", f"Your reset token: {token}")
    return MessageOut(message="If this email exists, a reset token was sent")

@router.post("/reset-password", response_model=MessageOut)
def reset_password(payload: ResetPasswordIn, db: OrmSession = Depends(get_db)):
    email = parse_reset_token(payload.token)
    if not email:
        raise HTTPException(status_code=400, detail="Invalid or expired token")
        user = db.execute(select(User).where(User.email == email)).scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if payload.new_password == settings.DEFAULT_PASSWORD:
        raise HTTPException(status_code=400, detail="New password cannot be the default password")
        user.hashed_password = hash_password(payload.new_password)
        user.is_first_login = False
        db.commit()
    return MessageOut(message="Password reset successful. Please log in.")