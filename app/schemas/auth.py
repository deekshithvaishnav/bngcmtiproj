from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime

class LoginIn(BaseModel):
	username: str
	password: str

class LoginSuccessOut(BaseModel):
	session_id: str
	role: str
	username: str
	expires_at: datetime

class FirstLoginRequiredOut(BaseModel):
	first_login_required: bool = True

class RoleInUseOut(BaseModel):
	role_in_use: bool
	locked_since: Optional[datetime] = None
	message: Optional[str] = None

class FirstLoginChangeIn(BaseModel):
	username: str
	old_password: str
	new_password: str

class RequestResetIn(BaseModel):
	email: EmailStr

class ResetPasswordIn(BaseModel):
	token: str
	new_password: str
