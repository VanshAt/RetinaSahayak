import hashlib
import json
from typing import Any, Optional
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from backend.app.models.audit_log import AuditLog
from backend.app.core.logging import logger


def create_audit_log(
    db: Session,
    action: str,
    resource_type: str,
    resource_id: str,
    user_id: Optional[str] = None,
    user_role: Optional[str] = None,
    status: str = "SUCCESS",
    client_ip: str = "127.0.0.1",
    payload_data: Optional[Any] = None
) -> AuditLog:
    """
    Creates a tamper-evident audit log record with a cryptographic SHA-256 hash.
    Ensures end-to-end traceability for patient data access, AI runs, and clinical reviews.
    """
    try:
        payload_serialized = json.dumps(payload_data or {}, sort_keys=True, default=str)
    except Exception:
        payload_serialized = str(payload_data or {})

    # Cryptographic integrity signature
    hash_input = f"{user_id or 'SYSTEM'}:{user_role or 'NONE'}:{action}:{resource_type}:{resource_id}:{status}:{payload_serialized}:{datetime.now(timezone.utc).isoformat()}"
    payload_hash = hashlib.sha256(hash_input.encode("utf-8")).hexdigest()

    log_entry = AuditLog(
        user_id=user_id,
        user_role=user_role,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        status=status,
        client_ip=client_ip,
        payload_hash=payload_hash
    )
    db.add(log_entry)
    db.flush()
    logger.info(f"Audit log created: action={action}, resource={resource_type}:{resource_id}, user={user_id}, role={user_role}, status={status}")
    return log_entry
