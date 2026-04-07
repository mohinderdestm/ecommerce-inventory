import os
from jose import jwt
from fastapi import HTTPException, Request
from dotenv import load_dotenv
from passlib.context import CryptContext
from datetime import datetime, timedelta

load_dotenv()

class SecurityManager:

    def __init__(self):
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        self.SECRET_KEY = os.getenv("JWT_SECRET_KEY")
        self.ALGORITHM = os.getenv("JWT_ALGORITHM")
        self.EXPIRY_MINUTES = int(os.getenv("JWT_EXPIRY_MINUTES", 30))

    def hash_password(self, password: str) -> str:
        return self.pwd_context.hash(password)

    def verify_password(self, plain: str, hashed: str) -> bool:
        return self.pwd_context.verify(plain, hashed)

    def create_access_token(self, payload: dict):
        to_encode = payload.copy()
        expire = datetime.utcnow() + timedelta(minutes=self.EXPIRY_MINUTES)

        to_encode.update({"exp": expire})

        return jwt.encode(to_encode, self.SECRET_KEY, algorithm=self.ALGORITHM)

    def create_refresh_token(self, payload: dict):
        to_encode = payload.copy()
        expire = datetime.utcnow() + timedelta(days=7)

        to_encode.update({"exp": expire, "type": "refresh"})

        return jwt.encode(to_encode, self.SECRET_KEY, algorithm=self.ALGORITHM)

    def verify_token(self, token: str):
        try:
            payload = jwt.decode(token, self.SECRET_KEY, algorithms=[self.ALGORITHM])
            return payload
        except Exception:
            return None

    def get_current_user(self, request: Request):
        access_token = request.cookies.get("access_token")

        if access_token:
            payload = self.verify_token(access_token)
            if payload:
                return payload

        raise HTTPException(status_code=401, detail="Not authenticated")


security = SecurityManager()


class RoleChecker:
    def __init__(self, allowed_roles):
        self.allowed_roles = allowed_roles

    def __call__(self, request: Request):
        token = request.cookies.get("access_token")

        if not token:
            raise HTTPException(status_code=401)

        payload = security.verify_token(token)

        if payload["role"] not in self.allowed_roles:
            raise HTTPException(status_code=403)

        return payload