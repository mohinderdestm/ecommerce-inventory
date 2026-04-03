from fastapi import Depends,HTTPException,status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from app.core.security import SECRET_KEY,ALGORITHM
from app.core.database import db
from bson import ObjectId

security = HTTPBearer()

async def get_current_user(
        credentials: HTTPAuthorizationCredentials = Depends(security)
):
    
        token = credentials.credentials

        try:
                payload = jwt.decode(token,SECRET_KEY, algorithms=[ALGORITHM])
                
                user_id =payload.get("user_id")

                if not user_id:
                        raise HTTPException(
                                status_code=status.HTTP_404_NOT_FOUND,
                                detail="Invalid token payload"
                        )
                
                user = await db["users"].find_one({"_id":ObjectId(user_id)})

                if not user:
                        raise HTTPException(
                                status_code=status.HTTP_404_NOT_FOUND,
                                detail="user not found"
                        )
                return user
                
        except JWTError:
               raise HTTPException(
                       status_code= status.HTTP_401_UNAUTHORIZED,
                       detail="Invalid or expired token"

               )
        
# Role-Based Access Function
def required_roles(allowed_roles:list):
        async def role_checker(user=Depends(get_current_user)):
                if user["role"] not in allowed_roles:
                        raise HTTPException(
                                status_code=status.HTTP_403_FORBIDDEN,
                                detail="You don't have permission"
                        )
                return user
        return role_checker