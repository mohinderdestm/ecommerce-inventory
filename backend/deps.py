from fastapi import Request, HTTPException
from auth import decode_token
from database import users_collection   # ⭐ ADD THIS
from bson import ObjectId

async def get_current_user(request: Request):
    token = request.cookies.get("token")

    if not token:
        raise HTTPException(status_code=401, detail="Not logged in")

    try:
        payload = decode_token(token)

        # ⭐ FETCH FULL USER FROM DB
        user = await users_collection.find_one({
            "email": payload.get("email")
        })

        if not user:
            raise HTTPException(status_code=401, detail="User not found")

        # ⭐ RETURN FULL USER
        return {
            "_id": str(user["_id"]),
            "email": user["email"],
            "role": user["role"],
            "warehouse_id": user.get("warehouse_id")   # 🔥 CRITICAL
        }

    except Exception as e:
        raise HTTPException(status_code=401, detail="Invalid token")


# from fastapi import Request, HTTPException,Depends
# from auth import decode_token

# async def get_current_user(request: Request):
#     token = request.cookies.get("token")

#     if not token:
#         raise HTTPException(status_code=401, detail="Not logged in")

#     try:
#         payload = decode_token(token)
#         return payload
#     except:
#         raise HTTPException(status_code=401, detail="Invalid token")


# def role_required(roles: list):
#     async def checker(user=Depends(get_current_user)):
#         if user["role"] not in roles:
#             raise HTTPException(status_code=403, detail="Not allowed")
#         return user
#     return checker