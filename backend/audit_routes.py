from fastapi import APIRouter, Depends
from deps import get_current_user
from database import audit_logs_collection

router = APIRouter(prefix="/audit-logs", tags=["Audit Logs"])


@router.get("")
async def get_audit_logs(user=Depends(get_current_user)):

    if user["role"] != "admin":
        return []

    logs = await audit_logs_collection.find().sort(
        "timestamp",
        -1
    ).to_list(200)

    data = []

    for log in logs:

        data.append({

            "id": str(log["_id"]),

            "time": str(
                log.get("timestamp", "")
            ),

            "user": log.get(
                "user_name",
                "Unknown"
            ),

            "role": log.get(
                "role",
                "-"
            ),

            "action": log.get(
                "action",
                "-"
            ),

            "message": log.get(
                "message",
                "-"
            )

        })

    return data