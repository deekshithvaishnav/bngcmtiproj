from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class SessionCheckOut(BaseModel):
	valid: bool
	username: Optional[str] = None
	role: Optional[str] = None
	expires_at: Optional[datetime] = None

class MessageOut(BaseModel):
	message: str
