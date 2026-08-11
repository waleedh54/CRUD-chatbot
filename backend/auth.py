import os
from datetime import datetime, timedelta
from jose import jwt, JWTError
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from dotenv import load_dotenv

from database import get_db
import crud

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY", "insecure-dev-key-change-me")
ALGORITHM = "HS256"
EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "120"))

security = HTTPBearer()


def create_access_token(email: str) -> str:
    expire = datetime.utcnow() + timedelta(minutes=EXPIRE_MINUTES)
    payload = {"sub": email, "exp": expire}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def _credentials_exception():
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired session. Please log in again.",
        headers={"WWW-Authenticate": "Bearer"},
    )


def get_current_admin(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
):
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
        if not email:
            raise _credentials_exception()
    except JWTError:
        raise _credentials_exception()

    admin = crud.get_admin_by_email(db, email)
    if not admin:
        raise _credentials_exception()
    return admin