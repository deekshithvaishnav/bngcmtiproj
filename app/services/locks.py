from datetime import datetime, timezone
from sqlalchemy.orm import Session as OrmSession
from sqlalchemy import select
from app.models.role_lock import RoleLock
from app.models.enums import UserRole
from app.models.session import Session as SessionModel

def get_active_lock(db: OrmSession, role: UserRole):
    lock = db.execute(select(RoleLock).where(RoleLock.role == role)).scalar_one_or_none()
    if not lock:
            return None
    if not lock.session_id:
            return None
    # Check if the linked session is still valid
    s = db.get(SessionModel, lock.session_id)
    if s is None or s.expires_at <= datetime.now(timezone.utc) or s.logout_at is not None:
        # Stale lock, clear it
        lock.session_id = None
        lock.user_id = None
        lock.expires_at = None
        db.commit()
        return None
    return lock

def acquire_lock(db: OrmSession, role: UserRole, session_row: SessionModel):
    # Ensure a lock row exists
    lock = db.execute(select(RoleLock).where(RoleLock.role == role)).scalar_one_or_none()
    if not lock:
        lock = RoleLock(role=role)
        db.add(lock)
        db.commit()
        db.refresh(lock)

        # Re-check if active
        active = get_active_lock(db, role)
    if active:
        return None

    # Acquire
    lock.session_id = session_row.id
    lock.user_id = session_row.user_id
    lock.expires_at = session_row.expires_at
    db.commit()
    db.refresh(lock)
    return lock

def release_lock_if_owner(db: OrmSession, role: UserRole, session_row: SessionModel):
    lock = db.execute(select(RoleLock).where(RoleLock.role == role)).scalar_one_or_none()
    if not lock:
        return
    if lock.session_id == session_row.id:
        lock.session_id = None
        lock.user_id = None
        lock.expires_at = None
        db.commit()
