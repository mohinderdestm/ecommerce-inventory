from pydantic import BaseModel,EmailStr,Field
from enum import Enum

class userRole(str,Enum):
    ADMIN ="admin"
    INVENTORY_MANAGER = "inventory_manager"
    WAREHOUSE_STAFF = "warehouse_staff"
    FINANCE_STAFF = "finance_staff"
    VIEWER = "viewer"
    SUPPLIER = "supplier" 

class RegisterSchema(BaseModel):
    name:str
    email:EmailStr
    password:str = Field(..., min_length=6, max_length=72)
    role:userRole

class loginSchema(BaseModel):
    email:EmailStr
    password:str
