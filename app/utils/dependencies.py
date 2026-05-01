from ipaddress import ip_address

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.core.security import decode_access_token
from app.core.database import users_collection

security = HTTPBearer()


def _normalize_ip(candidate: str | None) -> str | None:
    if not candidate:
        return None

    value = candidate.strip().strip('"')
    if not value or value.lower() == "unknown":
        return None

    if value.startswith("[") and "]" in value:
        value = value[1 : value.index("]")]
    elif value.count(":") == 1:
        host, port = value.rsplit(":", 1)
        if port.isdigit():
            value = host

    if "%" in value:
        value = value.split("%", 1)[0]

    try:
        return str(ip_address(value))
    except ValueError:
        return None


def _extract_forwarded_ip(forwarded_header: str | None) -> str | None:
    if not forwarded_header:
        return None

    for entry in forwarded_header.split(","):
        for part in entry.split(";"):
            key, separator, value = part.strip().partition("=")
            if separator and key.lower() == "for":
                ip_value = _normalize_ip(value)
                if ip_value:
                    return ip_value
    return None


def _get_client_ip(request: Request) -> str | None:
    header_candidates = [
        request.headers.get("cf-connecting-ip"),
        request.headers.get("true-client-ip"),
        request.headers.get("x-real-ip"),
    ]

    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        header_candidates.extend(forwarded_for.split(","))

    header_candidates.append(_extract_forwarded_ip(request.headers.get("forwarded")))
    header_candidates.append(request.client.host if request.client else None)

    for candidate in header_candidates:
        ip_value = _normalize_ip(candidate)
        if ip_value:
            return ip_value

    return None


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    token = credentials.credentials

    payload = decode_access_token(token)

    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )

    email = payload.get("sub")

    if not email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )

    user = await users_collection.find_one({"email": email})

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    return {
        "id": str(user["_id"]),
        "email": user["email"],
        "role": user.get("role", "viewer"),
        "name": user.get("name", ""),
    }


def require_role(required_roles: list):
    def role_checker(user=Depends(get_current_user)):
        if user.get("role") not in required_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required roles: {', '.join(required_roles)}",
            )
        return user

    return role_checker


async def get_request_audit_context(request: Request):
    client_host = request.client.host if request.client else None
    real_ip = _get_client_ip(request)
    return {
        "ip_address": real_ip,
        "method": request.method,
        "path": str(request.url.path),
        "user_agent": request.headers.get("user-agent"),
        "client_host": client_host,
        "forwarded_for": request.headers.get("x-forwarded-for"),
    }
