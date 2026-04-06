from datetime import datetime


def user_model(user) -> dict:
    return {
        "id": str(user["_id"]),
        "email": user.get("email"),
        "name": user.get("name", "User"),
        "role": user.get("role", "viewer"),
        "created_at": user.get("created_at", datetime.utcnow()),
    }
