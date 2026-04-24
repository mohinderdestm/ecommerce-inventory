from typing import Optional, List
from bson import ObjectId
from app.core.database import get_database

COLLECTION = "purchase_orders"

async def create_purchase_order(doc: dict) -> str:
    db = get_database()
    result = await db[COLLECTION].insert_one(doc)
    return str(result.inserted_id)

async def get_purchase_order(po_id: str) -> Optional[dict]:
    db = get_database()
    if not ObjectId.is_valid(po_id):
        return None
    po = await db[COLLECTION].find_one({"_id": ObjectId(po_id)})
    if po:
        po["_id"] = str(po["_id"])
    return po

async def update_purchase_order(po_id: str, updates: dict) -> bool:
    db = get_database()
    if not ObjectId.is_valid(po_id):
        return False
    result = await db[COLLECTION].update_one(
        {"_id": ObjectId(po_id)},
        {"$set": updates}
    )
    return result.modified_count > 0

async def list_purchase_orders(skip: int = 0, limit: int = 50, filters: dict = None) -> List[dict]:
    db = get_database()
    query = filters or {}
    cursor = db[COLLECTION].find(query).sort("created_at", -1).skip(skip).limit(limit)
    pos = await cursor.to_list(length=limit)
    for po in pos:
        po["_id"] = str(po["_id"])
    return pos

async def count_purchase_orders(filters: dict = None) -> int:
    db = get_database()
    query = filters or {}
    return await db[COLLECTION].count_documents(query)
