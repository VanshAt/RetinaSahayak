from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from backend.app.core.database import get_db
from backend.app.api.deps import require_role
from backend.app.models.user import User
from backend.app.models.audit_log import AuditLog
from backend.app.schemas.common import APIResponse
from backend.app.schemas.analytics import AuditLogResponse


router = APIRouter(prefix="/admin/audit-logs", tags=["Audit Log"])


@router.get("", response_model=APIResponse)
def list_audit_logs(
    action: Optional[str] = Query(None, description="Filter by action name"),
    resource_type: Optional[str] = Query(None, description="Filter by resource type"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["ADMIN"]))
):
    """
    Retrieves tamper-evident cryptographic audit logs. Accessible exclusively to Admins.
    """
    query = (
        db.query(AuditLog, User.email)
        .outerjoin(User, AuditLog.user_id == User.id)
    )

    if action:
        query = query.filter(AuditLog.action == action)
    if resource_type:
        query = query.filter(AuditLog.resource_type == resource_type)

    total = query.count()
    records = (
        query.order_by(desc(AuditLog.created_at))
        .offset(skip)
        .limit(limit)
        .all()
    )

    items = []
    for log, email in records:
        items.append({
            "id": log.id,
            "user_id": log.user_id,
            "user_email": email,
            "user_role": log.user_role or (log.user.role if log.user else None),
            "action": log.action,
            "resource_type": log.resource_type,
            "resource_id": log.resource_id,
            "status": getattr(log, "status", "SUCCESS"),
            "client_ip": log.client_ip,
            "payload_hash": log.payload_hash,
            "created_at": log.created_at.isoformat() if log.created_at else None
        })

    return APIResponse(
        success=True,
        data={
            "items": items,
            "total": total,
            "skip": skip,
            "limit": limit
        }
    )
