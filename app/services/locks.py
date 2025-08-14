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
    # Only allow lock if session is valid
    if lock.session_id is not None:
        # Check if the linked session is still valid
        s = db.get(SessionModel, lock.session_id)
        if s is None or s.expires_at <= datetime.now(timezone.utc) or s.logout_at is not None:
            # Stale lock, delete the row
            db.delete(lock)
            db.commit()
            return None
        # Session is valid, lock is active
        return lock
    # No active session, lock is not held
    return None

def acquire_lock(db: OrmSession, role: UserRole, session_row: SessionModel):
    lock = db.execute(select(RoleLock).where(RoleLock.role == role)).scalar_one_or_none()
    active = get_active_lock(db, role)
    if active:
        # Lock is held by another session, deny
        return None

    if not lock:
        # Create lock for this session
        lock = RoleLock(
            role=role,
            session_id=session_row.id
        )
        db.add(lock)
        db.commit()
        db.refresh(lock)
        return lock

    # Acquire lock for this session
    lock.session_id = session_row.id
    db.commit()
    db.refresh(lock)
    return lock

def release_lock_if_owner(db: OrmSession, role: UserRole, session_row: SessionModel):
    lock = db.execute(select(RoleLock).where(RoleLock.role == role)).scalar_one_or_none()
    if not lock:
        return
    if lock.session_id == session_row.id:
        db.delete(lock)
        db.commit()
