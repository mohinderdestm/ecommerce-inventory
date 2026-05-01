import logging
from typing import Optional, Dict, Any

from app.repositories.audit_log_repository import AuditLogRepository
from app.models.audit_log import build_audit_log_document
from app.core.context import request_ip_ctx

logger = logging.getLogger(__name__)

class AuditLogService:
    def __init__(self, audit_log_repo: AuditLogRepository):
        self.audit_log_repo = audit_log_repo

    async def log_action(
        self,
        user_id: str,
        action: str,
        entity_type: str,
        entity_id: str,
        old_value: Optional[Dict[str, Any]] = None,
        new_value: Optional[Dict[str, Any]] = None,
    ) -> None:
        try:
            ip_address = request_ip_ctx.get()
            
            # Simple diff creation to save space if needed, 
            # but requirements say "old value", "new value". We will log them directly.
            
            doc = build_audit_log_document(
                user_id=user_id,
                action=action,
                entity_type=entity_type,
                entity_id=entity_id,
                old_value=old_value,
                new_value=new_value,
                ip_address=ip_address,
            )
            
            await self.audit_log_repo.create(doc)
            logger.info(f"Audit log created | User: {user_id} | Action: {action} | Entity: {entity_type} ({entity_id})")
        except Exception as e:
            logger.error(f"Failed to create audit log: {str(e)}")

    async def list_logs(
        self,
        entity_type: Optional[str] = None,
        user_id: Optional[str] = None,
        action: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> dict:
        skip = (page - 1) * page_size
        logs, total = await self.audit_log_repo.search(
            entity_type=entity_type,
            user_id=user_id,
            action=action,
            skip=skip,
            limit=page_size
        )
        return {"total": total, "page": page, "page_size": page_size, "logs": logs}
