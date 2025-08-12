from sqlalchemy.orm import Session as OrmSession
from app.models.notification import Notification

def notify_user(db: OrmSession, user_id: int | None, role: str | None, title: str, description: str | None = None, target_url: str | None = None):
    n = Notification(user_id=user_id, role=role, title=title, description=description, target_url=target_url)
    db.add(n)
    db.commit()