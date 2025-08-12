from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session as OrmSession
from sqlalchemy import select, func
from app.api.deps import require_role, get_current_session
from app.db.session import get_db
from app.models.enums import UserRole, RequestStatus
from app.models.inventory import ToolInventory
from app.models.tool_requests import ToolUsageRequest
from app.schemas.inventory import ToolListItem
from app.schemas.tool_requests import ToolUsageCreateIn, ToolUsageShortOut
from app.services.id_generator import make_request_id

router = APIRouter()

@router.get("/tools", response_model=list[ToolListItem], dependencies=[Depends(require_role(UserRole.OPERATOR))])
def list_available_tools(db: Session = Depends(get_db)):
    rows = db.execute(
    select(ToolInventory)
    .where(ToolInventory.quantity_available > 0)
    .order_by(ToolInventory.name.asc())
    ).scalars().all()
    return [
    ToolListItem(
    tool_id=r.id,
    name=r.name,
    make=r.make,
    range_mm=r.range_mm,
    location=r.location,
    quantity_available=r.quantity_available
    ) for r in rows
    ]

@router.post("/tool-requests", response_model=ToolUsageShortOut, dependencies=[Depends(require_role(UserRole.OPERATOR))])
def create_tool_request(payload: ToolUsageCreateIn, data=Depends(get_current_session), db: Session = Depends(get_db)):
    sess, operator = data
    inv = db.get(ToolInventory, payload.tool_id)
    if not inv:
        raise HTTPException(status_code=404, detail="Tool not found")
    if payload.requested_qty <= 0:
        raise HTTPException(status_code=400, detail="Invalid quantity")
    if payload.requested_qty > inv.quantity_available:
        raise HTTPException(status_code=400, detail="Requested quantity exceeds available")
    next_id = (db.execute(select(func.max(ToolUsageRequest.id))).scalar() or 0) + 1
    rid = make_request_id("TR", next_id)

    row = ToolUsageRequest(
        request_id=rid,
        operator_id=operator.id,
        tool_id=inv.id,
        requested_qty=payload.requested_qty,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return ToolUsageShortOut(
        request_id=row.request_id,
        tool_id=row.tool_id,
        tool_name=inv.name,
        requested_qty=row.requested_qty,
        status=row.status.value,
        requested_at=row.requested_at,
    )

@router.post("/tool-requests/{request_id}/mark-received", dependencies=[Depends(require_role(UserRole.OPERATOR))])
def mark_received(request_id: str, data=Depends(get_current_session), db: Session = Depends(get_db)):
    sess, operator = data
    req = db.execute(select(ToolUsageRequest).where(ToolUsageRequest.request_id == request_id)).scalar_one_or_none()
    if not req:
        raise HTTPException(status_code=404, detail="Request not found")
    if req.operator_id != operator.id:
        raise HTTPException(status_code=403, detail="Forbidden")
    if req.status != RequestStatus.APPROVED:
        raise HTTPException(status_code=400, detail="Request not approved")
    from datetime import datetime, timezone
    req.status = RequestStatus.RECEIVED
    req.received_at = datetime.now(timezone.utc)
    db.commit()
    return {"message": "Marked received"}

@router.post("/tool-requests/{request_id}/return", dependencies=[Depends(require_role(UserRole.OPERATOR))])
def return_tool(request_id: str, data=Depends(get_current_session), db: Session = Depends(get_db)):
    sess, operator = data
    req = db.execute(select(ToolUsageRequest).where(ToolUsageRequest.request_id == request_id)).scalar_one_or_none()
    if not req:
        raise HTTPException(status_code=404, detail="Request not found")
    if req.operator_id != operator.id:
        raise HTTPException(status_code=403, detail="Forbidden")
    if req.status != RequestStatus.RECEIVED:
        raise HTTPException(status_code=400, detail="Tool not in received status")
    inv = db.get(ToolInventory, req.tool_id)
    if not inv:
        raise HTTPException(status_code=404, detail="Tool not found")
    inv.quantity_available += req.requested_qty
    from datetime import datetime, timezone
    req.status = RequestStatus.RETURNED
    req.returned_at = datetime.now(timezone.utc)
    db.commit()
    return {"message": "Returned"}