from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session as OrmSession
from sqlalchemy import select, func, text
from app.api.deps import require_role, get_current_session
from app.db.session import get_db
from app.models.enums import UserRole, RequestStatus
from app.models.tool_requests import ToolUsageRequest, ToolAdditionRequest
from app.models.inventory import ToolInventory
from app.schemas.tool_requests import ApproveToolUsageOut
from app.schemas.inventory import ToolAdditionCreateIn, ToolAdditionOut
from app.services.id_generator import make_request_id

router = APIRouter()

@router.get("/tool-requests", dependencies=[Depends(require_role(UserRole.SUPERVISOR))])
def list_pending_tool_requests(db: Session = Depends(get_db)):
    rows = db.execute(
    select(ToolUsageRequest)
    .where(ToolUsageRequest.status == RequestStatus.PENDING)
    .order_by(ToolUsageRequest.requested_at.asc())
    ).scalars().all()
    return [
    {
    "request_id": r.request_id,
    "operator_id": r.operator_id,
    "operator_username": r.operator.username if r.operator else None,
    "tool_id": r.tool_id,
    "tool_name": r.tool.name if r.tool else None,
    "requested_qty": r.requested_qty,
    "requested_at": r.requested_at,
    } for r in rows
    ]

@router.post("/tool-requests/{request_id}/approve", response_model=ApproveToolUsageOut, dependencies=[Depends(require_role(UserRole.SUPERVISOR))])
def approve_tool_request(request_id: str, data=Depends(get_current_session), db: Session = Depends(get_db)):
    sess, user = data
    req = db.execute(select(ToolUsageRequest).where(ToolUsageRequest.request_id == request_id)).scalar_one_or_none()
    if not req:
        raise HTTPException(status_code=404, detail="Request not found")
    if req.status != RequestStatus.PENDING:
        raise HTTPException(status_code=400, detail="Request already processed")
    inv = db.get(ToolInventory, req.tool_id)
    if not inv:
        raise HTTPException(status_code=404, detail="Tool not found")

    # Lock table row to avoid race (Postgres)
    db.execute(text("LOCK TABLE tool_inventory IN ROW EXCLUSIVE MODE"))
    db.refresh(inv)

    if inv.quantity_available < req.requested_qty:
        raise HTTPException(status_code=400, detail="Insufficient stock at approval time")

    inv.quantity_available -= req.requested_qty
    req.status = RequestStatus.APPROVED
    from datetime import datetime, timezone
    req.reviewed_at = datetime.now(timezone.utc)
    req.approved_by = user.id
    req.supervisor_id = user.id

    db.commit()

    return ApproveToolUsageOut(
        request_id=req.request_id,
        status=req.status.value,
        tool_id=inv.id,
        tool_name=inv.name,
        requested_qty=req.requested_qty,
        remaining_qty=inv.quantity_available,
        approved_at=req.reviewed_at,
        approved_by={"id": user.id, "name": user.full_name},
    )

@router.post("/tool-requests/{request_id}/reject", dependencies=[Depends(require_role(UserRole.SUPERVISOR))])
def reject_tool_request(request_id: str, reason: str = "Not approved", db: Session = Depends(get_db)):
    req = db.execute(select(ToolUsageRequest).where(ToolUsageRequest.request_id == request_id)).scalar_one_or_none()
    if not req:
        raise HTTPException(status_code=404, detail="Request not found")
    if req.status != RequestStatus.PENDING:
        raise HTTPException(status_code=400, detail="Request already processed")
    from datetime import datetime, timezone
    req.status = RequestStatus.REJECTED
    req.reviewed_at = datetime.now(timezone.utc)
    req.reviewer_remarks = reason
    db.commit()
    return {"message": "Rejected"}

@router.post("/tool-additions", response_model=ToolAdditionOut, dependencies=[Depends(require_role(UserRole.SUPERVISOR))])
def create_tool_addition(payload: ToolAdditionCreateIn, data=Depends(get_current_session), db: Session = Depends(get_db)):
    sess, supervisor = data
    next_id = (db.execute(select(func.max(ToolAdditionRequest.id))).scalar() or 0) + 1
    rid = make_request_id("TAR", next_id)
    row = ToolAdditionRequest(
    request_id=rid,
    tool_name=payload.tool_name,
    make=payload.make,
    range_mm=payload.range_mm,
    quantity=payload.quantity,
    location=payload.location,
    supervisor_id=supervisor.id,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return ToolAdditionOut(
    request_id=row.request_id,
    tool_name=row.tool_name,
    make=row.make,
    range_mm=row.range_mm,
    quantity=row.quantity,
    location=row.location,
    status=row.status.value,
    requested_at=row.requested_at,
    )

@router.get("/logs/approved-usage", dependencies=[Depends(require_role(UserRole.SUPERVISOR))])
def approved_usage_logs(db: Session = Depends(get_db)):
    rows = db.execute(
    select(ToolUsageRequest)
    .where(ToolUsageRequest.status == RequestStatus.APPROVED)
    .order_by(ToolUsageRequest.reviewed_at.desc())
    ).scalars().all()
    return [
    {
    "request_id": r.request_id,
    "tool": r.tool.name if r.tool else None,
    "quantity": r.requested_qty,
    "operator_id": r.operator_id,
    "operator_username": r.operator.username if r.operator else None,
    "supervisor_id": r.approved_by,
    "supervisor_name": r.approver.full_name if r.approver else None,
    "requested_at": r.requested_at,
    "approved_at": r.reviewed_at,
    } for r in rows
    ]
