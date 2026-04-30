from datetime import datetime
from typing import Any, Optional

from bson import ObjectId
from fastapi import HTTPException

from app.models.audit_log_model import audit_log_model
from app.repositories.audit_repository import AuditRepository


class AuditService:
    VIEW_ROLES = {"admin", "manager"}

    @staticmethod
    def _check_view_access(user: dict):
        if user.get("role") not in AuditService.VIEW_ROLES:
            raise HTTPException(status_code=403, detail="Access denied")

    @staticmethod
    def _serialize(value: Any):
        if isinstance(value, ObjectId):
            return str(value)
        if isinstance(value, datetime):
            return value.isoformat()
        if isinstance(value, list):
            return [AuditService._serialize(item) for item in value]
        if isinstance(value, dict):
            return {
                str(key): AuditService._serialize(item) for key, item in value.items()
            }
        return value

    @staticmethod
    def _actor(user: Optional[dict]):
        if not user:
            return {"id": None, "name": "System", "email": None, "role": "system"}
        return {
            "id": user.get("id"),
            "name": user.get("name"),
            "email": user.get("email"),
            "role": user.get("role"),
        }

    @staticmethod
    def _request_metadata(audit_context: Optional[dict]):
        audit_context = audit_context or {}
        return {
            "method": audit_context.get("method"),
            "path": audit_context.get("path"),
            "user_agent": audit_context.get("user_agent"),
        }

    @staticmethod
    async def log_action(
        *,
        user: Optional[dict],
        action: str,
        entity_type: str,
        entity_id: Optional[str] = None,
        old_value: Any = None,
        new_value: Any = None,
        audit_context: Optional[dict] = None,
    ):
        actor = AuditService._actor(user)
        document = {
            "user_id": actor.get("id"),
            "user": actor,
            "action": action,
            "entity_type": entity_type,
            "entity_id": str(entity_id) if entity_id is not None else None,
            "old_value": AuditService._serialize(old_value),
            "new_value": AuditService._serialize(new_value),
            "timestamp": datetime.utcnow(),
            "ip_address": (audit_context or {}).get("ip_address"),
            "request_metadata": AuditService._request_metadata(audit_context),
        }
        await AuditRepository.create(document)

    @staticmethod
    async def safe_log_action(**kwargs):
        try:
            await AuditService.log_action(**kwargs)
        except Exception:
            return None

    @staticmethod
    async def list_logs(
        user: dict,
        *,
        entity_type: Optional[str] = None,
        entity_id: Optional[str] = None,
        action: Optional[str] = None,
        user_id: Optional[str] = None,
        limit: int = 200,
    ):
        AuditService._check_view_access(user)

        query = {}
        if entity_type:
            query["entity_type"] = entity_type
        if entity_id:
            query["entity_id"] = entity_id
        if action:
            query["action"] = action
        if user_id:
            query["user_id"] = user_id

        rows = await AuditRepository.list_logs(query, limit=limit)
        return [audit_log_model(row) for row in rows]
