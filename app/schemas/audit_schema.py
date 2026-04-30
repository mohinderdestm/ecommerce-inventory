from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


class AuditLogResponse(BaseModel):
    id: str
    user_id: Optional[str] = None
    user: dict[str, Any] = Field(default_factory=dict)
    action: str
    entity_type: str
    entity_id: Optional[str] = None
    old_value: Any = None
    new_value: Any = None
    timestamp: datetime
    ip_address: Optional[str] = None
    request_metadata: dict[str, Any] = Field(default_factory=dict)
