from sqlalchemy.orm import Session as OrmSession
from app.core.config import settings
from app.core.security import hash_password
from app.models.user import User, UserRole

def seed_initial_officer(db: Session, username: str, full_name: str, email: str, contact_number: str):
    existing = db.query(User).filter(User.username == username).first()
    if existing:
        return existing
    user = User(
        username=username,
        full_name=full_name,
        email=email,
        contact_number=contact_number,
        role=UserRole.OFFICER,
        hashed_password=hash_password(settings.DEFAULT_PASSWORD),
        is_first_login=True,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user