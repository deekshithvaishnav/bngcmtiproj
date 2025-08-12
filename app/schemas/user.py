from pydantic import BaseModel, EmailStr
from typing import Optional

class UserCreateIn(BaseModel):
	username: str
	full_name: str
	email: EmailStr
	contact_number: str
	role: str
	password: str

class UserOut(BaseModel):
	id: int
	username: str
	full_name: str
	email: EmailStr
	contact_number: str
	role: str
	is_active: bool
