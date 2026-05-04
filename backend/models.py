from pydantic import BaseModel, EmailStr
from typing import Optional

class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str
    role: str 

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserOut(BaseModel):
    name: str
    email: str
    role: str

class Warehouse(BaseModel):
    name: str
    code: str
    address: str
    city: str
    state: str
    country: str
    pincode: str
    manager_id: Optional[str] = None

class AssignStaff(BaseModel):
    warehouse_id: str
    user_id: str
    role: str = "staff"

class AssignWarehouse(BaseModel):
    order_id: str
    warehouse_id: str