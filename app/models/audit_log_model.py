def audit_log_model(document: dict) -> dict:
    return {
        "id": str(document.get("_id")),
        "user_id": document.get("user_id"),
        "user": document.get("user"),
        "action": document.get("action"),
        "entity_type": document.get("entity_type"),
        "entity_id": document.get("entity_id"),
        "old_value": document.get("old_value"),
        "new_value": document.get("new_value"),
        "timestamp": document.get("timestamp"),
        "ip_address": document.get("ip_address"),
        "request_metadata": document.get("request_metadata") or {},
    }
