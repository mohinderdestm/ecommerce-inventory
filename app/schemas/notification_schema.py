from datetime import datetime
from typing import Optional, List, Literal

from pydantic import BaseModel, Field


NotificationSeverity = Literal["info", "warning", "critical"]


class NotificationCreate(BaseModel):
    type: str
    title: str
    message: str
    severity: NotificationSeverity = "info"
    target_roles: List[str] = []
    target_users: List[str] = []
    reference_type: Optional[str] = None
    reference_id: Optional[str] = None
    metadata: dict = {}
    dedupe_key: Optional[str] = None
    channels: List[str] = ["in_app"]


class NotificationResponse(BaseModel):
    id: str
    type: str
    title: str
    message: str
    severity: str
    target_roles: List[str]
    target_users: List[str]
    reference_type: Optional[str]
    reference_id: Optional[str]
    metadata: dict
    channels: List[str]
    email_simulation: Optional[dict] = None
    is_read: bool = False
    read_at: Optional[datetime] = None
    created_at: Optional[datetime]
    updated_at: Optional[datetime]


class NotificationListResponse(BaseModel):
    items: List[NotificationResponse]
    unread_count: int = Field(default=0, ge=0)
