from fastapi import APIRouter, Depends, HTTPException
from bson import ObjectId

from database import notifications_collection
from deps import get_current_user

router = APIRouter(
    prefix="/notifications",
    tags=["Notifications"]
)


def serialize(n):

    return {
        "id": str(n["_id"]),
        "user_email": n.get("user_email"),
        "title": n.get("title"),
        "message": n.get("message"),
        "type": n.get("type", "general"),
        "read": n.get("read", False),
        "created_at": n.get("created_at")
    }


@router.get("")
async def get_notifications(
    user=Depends(get_current_user)
):

    data = await notifications_collection.find({
        "user_email": user["email"]
    }).sort("_id", -1).to_list(100)

    return {
        "data": [serialize(n) for n in data]
    }


@router.get("/unread/count")
async def unread_count(
    user=Depends(get_current_user)
):

    count = await notifications_collection.count_documents({
        "user_email": user["email"],
        "read": False
    })

    return {
        "count": count
    }


@router.put("/{notification_id}/read")
async def mark_read(
    notification_id: str,
    user=Depends(get_current_user)
):

    notification = await notifications_collection.find_one({
        "_id": ObjectId(notification_id)
    })

    if not notification:
        raise HTTPException(status_code=404)

    if notification["user_email"] != user["email"]:
        raise HTTPException(status_code=403)

    await notifications_collection.update_one(
        {"_id": ObjectId(notification_id)},
        {
            "$set": {
                "read": True
            }
        }
    )

    return {
        "message": "Marked as read"
    }


@router.put("/read-all")
async def mark_all_read(
    user=Depends(get_current_user)
):

    await notifications_collection.update_many(
        {
            "user_email": user["email"],
            "read": False
        },
        {
            "$set": {
                "read": True
            }
        }
    )

    return {
        "message": "All notifications marked read"
    }


@router.delete("/{notification_id}")
async def delete_notification(
    notification_id: str,
    user=Depends(get_current_user)
):

    notification = await notifications_collection.find_one({
        "_id": ObjectId(notification_id)
    })

    if not notification:
        raise HTTPException(status_code=404)

    if notification["user_email"] != user["email"]:
        raise HTTPException(status_code=403)

    await notifications_collection.delete_one({
        "_id": ObjectId(notification_id)
    })

    return {
        "message": "Deleted"
    }
