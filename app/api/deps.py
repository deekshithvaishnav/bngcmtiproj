from datetime import datetime, timezone
from arrow import now
from fastapi import Depends, Header, HTTPException, status
from matplotlib.pyplot import arrow
from sqlalchemy.orm import Session as OrmSession
from sqlalchemy import select
from app.db.session import get_db
from app.models import user
from app.models.session import Session as SessionModel
from app.models.user import User
from app.models.enums import UserRole, SessionEndReason
from app.services.locks import release_lock_if_owner

def get_current_session(
    db: Session = Depends(get_db),
    x_session_id: str | None = Header(None)
    ) -> tuple[SessionModel, User]:
    if not x_session_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing session")
    sess = db.execute(select(SessionModel).where(SessionModel.session_id == x_session_id)).scalar_one_or_none()
    if not sess:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid session")
    now = arrow.now()
    if sess.expires_at <= now or sess.logout_at is not None:
        # mark expired if needed
        if sess.logout_at is None:
            sess.logout_at = sess.expires_at
            sess.ended_reason = SessionEndReason.EXPIRED
            db.commit()
        # release role lock if held
        if sess.role in (UserRole.OFFICER, UserRole.SUPERVISOR):
            release_lock_if_owner(db, sess.role, sess)
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Session expired")
        user = db.get(User, sess.user_id)
        if not user or not user.is_active:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User inactive")
    return sess, user

def require_role(required: UserRole):
    def checker(data=Depends(get_current_session)):
        sess, user = data
        if user.role != required:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
        return sess, user
    return checker