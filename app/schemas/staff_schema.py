from pydantic import BaseModel, EmailStr
from typing import Optional, List


class StaffCreate(BaseModel):
    name: str
    email: EmailStr
    phone: Optional[str]
    role: str


class StaffUpdate(BaseModel):
    name: Optional[str]
    email: Optional[EmailStr]
    phone: Optional[str]
    role: Optional[str]
    is_active: Optional[bool]


class StaffResponse(BaseModel):
    id: str
    name: str
    email: str
    phone: Optional[str]
    role: str
    is_active: bool


class BulkStaffCreate(BaseModel):
    staff: List[StaffCreate]
