from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class ToolListItem(BaseModel):
	id: int
	tool_name: str
	quantity: int
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class ToolAdditionCreateIn(BaseModel):
	tool_name: str
	quantity: int

class ToolAdditionOut(BaseModel):
	id: int
	tool_name: str
	status: str
	requested_by: int
	created_at: datetime

class ApproveToolAdditionOut(BaseModel):
	id: int
	tool_name: str
	status: str
	approved_by: Optional[int] = None
	approved_at: Optional[datetime] = None
