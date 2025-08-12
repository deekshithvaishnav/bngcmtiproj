from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session as OrmSession
from sqlalchemy import select
from app.api.deps import get_current_session
from app.db.session import get_db
from app.models.notification import Notification
from app.schemas.notification import NotificationOut

router = APIRouter()

@router.get("", response_model=list[NotificationOut])
def list_notifications(data=Depends(get_current_session), db: OrmSession = Depends(get_db)):
    sess, user = data
    rows = db.execute(
    select(Notification)
    .where((Notification.user_id == user.id) | (Notification.role == user.role.value))
    .order_by(Notification.created_at.desc())
    ).scalars().all()
    return rows

@router.post("/{notif_id}/mark-read")
def mark_read(notif_id: int, data=Depends(get_current_session), db: OrmSession = Depends(get_db)):
    n = db.get(Notification, notif_id)
    if not n:
        return {"message": "OK"}
    n.is_read = True
    db.commit()
    return {"message": "OK"}