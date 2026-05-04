from fastapi import HTTPException, status
from app.repositories.auth_repository import AuthRepository
from app.core.security import hash_password, verify_password, create_access_token

from app.repositories.supplier_repository import SupplierRepository
from app.services.supplier_service import SupplierService
from app.core.database import db
from app.services.audit_service import AuditService


class AuthService:

    def __init__(self):
        self.repo = AuthRepository()

    async def register(self, user):

        existing = await self.repo.get_by_email(user.email)

        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already exists"
            )

        user_dict = user.dict()
        user_dict["password"] = hash_password(user.password)

        user_id = await self.repo.create_user(user_dict)
        
        # ✅ CREATE SUPPLIER ROLE 
        if user.role == "supplier":
            supplier_repo = SupplierRepository(db)
            supplier_service = SupplierService(supplier_repo)

            await supplier_service.create_supplier_for_user(
                user_id,
                {
                     "name": user.name,
                      "email": user.email
                }
                
            )

        token = create_access_token({
        "user_id": str(user_id),
        "role": user.role
    })
        
        await AuditService.log(
            user_id=str(user_id),
            action="REGISTER",
            entity_type="user",
            entity_id=str(user_id),
            value=user_dict
        )

       
        return {
            "success": True,
            "message": "User registered successfully",
            "user_id": user_id,
            "access_token": token 
        }

    async def login(self, user):

        db_user = await self.repo.get_by_email(user.email)

        if not db_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        if not verify_password(user.password, db_user["password"]):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )
            
        await AuditService.log(
            user_id=str(db_user["_id"]),
            action="LOGIN",
            entity_type="user",
            entity_id=str(db_user["_id"]),
            value={"email": db_user["email"]},
            # ip=ip
         )

        token = create_access_token({
            "user_id": str(db_user["_id"]),
            "role": db_user["role"]
        })
        
        

        return {
            "success": True,
            "access_token": token,
            "token_type": "bearer",
            "user": {
               "id": str(db_user["_id"]),
               "email": db_user["email"],
               "role": db_user["role"],
               "name": db_user.get("name")
           }
        }