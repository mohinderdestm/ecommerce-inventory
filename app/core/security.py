
from passlib.context import CryptContext
from jose import jwt, JWTError, ExpiredSignatureError
from datetime import datetime, timedelta
from dotenv import load_dotenv
import os

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

# Load env variables
load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Auth scheme
security = HTTPBearer()


# =========================
# PASSWORD FUNCTIONS
# =========================

def hash_password(password: str) -> str:
    return pwd_context.hash(password[:72])  # bcrypt limit protection


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


# =========================
# TOKEN CREATION
# =========================

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})

    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


# =========================
# TOKEN VALIDATION (IMPORTANT)
# =========================

def validate_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

        return {
            "user_id": payload.get("user_id"),
            "email": payload.get("email"),
            "role": payload.get("role", "user"),
        }

    except ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired"
        )

    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )