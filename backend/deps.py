from fastapi import Request, HTTPException
from auth import decode_token
from database import users_collection   # ⭐ ADD THIS
from bson import ObjectId

async def get_current_user(request: Request):
    token = request.cookies.get("token")
    # print("TOKEN:", token) 

    if not token:
        raise HTTPException(status_code=401, detail="Not logged in")

    try:
        payload = decode_token(token)
        email = payload.get("email") or payload.get("sub")

        # ⭐ FETCH FULL USER FROM DB
        user = await users_collection.find_one({
             "email": email
        })

        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        
        user["id"] = str(user["_id"])

        # ⭐ RETURN FULL USER
        return {
            "id": str(user["_id"]),
            "_id": str(user["_id"]),
            "email": user["email"],
            "role": user["role"],
            "warehouse_id": user.get("warehouse_id")   # 🔥 CRITICAL
        }

    except Exception as e:
        raise HTTPException(status_code=401, detail="Invalid token")