from pydantic import BaseModel, EmailStr
from typing import Optional

class SupplierCreate(BaseModel):
    name: str
    contact_person: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    address: Optional[str] = None
    gst_number: Optional[str] = None
    payment_terms: Optional[str] = "Net 30"
    
class SupplierUpdate(BaseModel):
    name: Optional[str] = None
    contact_person: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    address: Optional[str] = None
    gst_number: Optional[str] = None
    payment_terms: Optional[str] = None