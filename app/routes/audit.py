
from fastapi import APIRouter, Depends
from app.core.database import get_db
from bson import ObjectId
from datetime import datetime

router = APIRouter(prefix="/audit", tags=["Audit"])


def serialize_doc(doc):
    """Convert Mongo document to JSON safe"""
    for key, value in doc.items():
        if isinstance(value, ObjectId):
            doc[key] = str(value)

        elif isinstance(value, datetime):
            doc[key] = value.isoformat()

        elif isinstance(value, dict):
            doc[key] = serialize_doc(value)

        elif isinstance(value, list):
            doc[key] = [
                serialize_doc(i) if isinstance(i, dict) else str(i) if isinstance(i, ObjectId) else i
                for i in value
            ]

    return doc



# @router.get("/")
# async def get_audit_logs(db=Depends(get_db)):
#     logs = await db["audit_logs"].find().sort("timestamp", -1).to_list(100)

#     # ✅ STEP 1: collect all user_ids
#     user_ids = list(set([log.get("user_id") for log in logs if log.get("user_id")]))

#     # ✅ STEP 2: convert to ObjectId safely
#     object_ids = []
#     for uid in user_ids:
#         try:
#             object_ids.append(ObjectId(uid))
#         except:
#             pass  # skip invalid ids

#     # ✅ STEP 3: fetch users
#     users = await db["users"].find({"_id": {"$in": object_ids}}).to_list(100)

#     # ✅ STEP 4: create map
#     user_map = {str(u["_id"]): u.get("name", "Unknown") for u in users}

#     # ✅ STEP 5: attach user_name to logs
#     for log in logs:
#         uid = str(log.get("user_id"))
#         log["user_id"] = uid
#         log["user_name"] = user_map.get(uid, "Unknown")

#     # ✅ STEP 6: serialize safely
#     safe_logs = [serialize_doc(log) for log in logs]

#     return safe_logs

@router.get("/")
async def get_audit_logs(
    search: str = "",
    action: str = "",
    db=Depends(get_db)
):
    filters = {}

    # SEARCH (action + entity_type)
    if search:
        filters["$or"] = [
            {"action": {"$regex": search, "$options": "i"}},
            {"entity_type": {"$regex": search, "$options": "i"}},
            {"entity_id": {"$regex": search, "$options": "i"}}
        ]

    
    if action:
        filters["action"] = {"$regex": action, "$options": "i"}
        
    print("SEARCH:", search)
    print("ACTION:", action)
    print("FILTERS:", filters)

    logs = await db["audit_logs"] \
        .find(filters) \
        .sort("timestamp", -1) \
        .to_list(100)

    # 🔥 ADD USER NAME
    user_ids = list(set([log.get("user_id") for log in logs if log.get("user_id")]))

    users = await db["users"].find({
        "_id": {"$in": [ObjectId(uid) for uid in user_ids]}
    }).to_list(100)

    user_map = {str(u["_id"]): u.get("name", "Unknown") for u in users}

    for log in logs:
        log["user_name"] = user_map.get(log.get("user_id"), "Unknown")

    safe_logs = [serialize_doc(log) for log in logs]

    return {
        "data": safe_logs
    }