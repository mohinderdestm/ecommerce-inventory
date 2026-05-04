
from fastapi import APIRouter, Depends, HTTPException

from deps import get_current_user
from database import email_logs_collection

router = APIRouter(
    tags=["Emails"]
)


def serialize(email):

    return {

        "id": str(email["_id"]),

        "to": email.get("to"),

        "subject": email.get("subject"),

        "message": email.get("message"),

        "type": email.get("type"),

        "status": email.get("status"),

        "created_at": email.get("created_at")

    }



@router.get("/emails")
async def get_my_emails(
    user=Depends(get_current_user)
):

    emails = await email_logs_collection.find({

        "to": user["email"]

    }).sort("_id", -1).to_list(500)

    return {

        "data": [
            serialize(e)
            for e in emails
        ]

    }



@router.get("/admin/email-logs")
async def get_all_email_logs(
    user=Depends(get_current_user)
):

    if user["role"] != "admin":

        raise HTTPException(
            status_code=403,
            detail="Admin only"
        )

    emails = await email_logs_collection.find({

        "to": user["email"]

    }).sort("_id", -1).to_list(1000)

    return {

        "data": [
            serialize(e)
            for e in emails
        ]

    }
