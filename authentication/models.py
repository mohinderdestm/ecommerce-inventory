from datetime import datetime
from enum import Enum

class Role(str, Enum):
    ADMIN = "Admin"
    INVENTORY = "Inventory"
    MANAGER = "Manager"
    WAREHOUSE = "Warehouse Staff"
    FINANCE = "Finance Staff"
    VIEWER = "Viewer"

class UserDB:
    def __init__(self, name, email, password,role=Role.VIEWER):
        self.name = name
        self.email = email
        self.password = password
        self.role = role
        self.created_at = datetime.utcnow()

    def to_dict(self):
        return self.__dict__