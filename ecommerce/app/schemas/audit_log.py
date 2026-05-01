from pydantic import BaseModel, Field
from typing import Optional, Any, Dict
from datetime import datetime

class AuditLogResponse(BaseModel):
    id: str = Field(alias="_id")
    user_id: str
    action: str
    entity_type: str
    entity_id: str
    old_value: Optional[Dict[str, Any]] = None
    new_value: Optional[Dict[str, Any]] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    timestamp: datetime

    class Config:
        populate_by_name = True

class AuditLogListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    logs: list[AuditLogResponse]
