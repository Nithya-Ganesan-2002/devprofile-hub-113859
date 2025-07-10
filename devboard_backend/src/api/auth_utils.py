"""JWT authentication and password hashing utilities for DevBoard FastAPI backend."""

from datetime import datetime, timedelta
from typing import Optional, Dict
from fastapi import HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import EmailStr
from .models import UserOut

# JWT configs (in production, load from env)
SECRET_KEY = "secret_key_for_devboard"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 3  # 3 days

# Password hashing context (bcrypt)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

# Mock in-memory user store: {email: {"id": int, "email": str, "hashed_password": str}}
user_store: Dict[str, Dict] = {}
user_id_counter = 1

# PUBLIC_INTERFACE
def verify_password(plain_password, hashed_password):
    """Verify user plaintext password vs stored."""
    return pwd_context.verify(plain_password, hashed_password)

# PUBLIC_INTERFACE
def get_password_hash(password):
    """Hash user password for storage."""
    return pwd_context.hash(password)

# PUBLIC_INTERFACE
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create JWT for authentication."""
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# PUBLIC_INTERFACE
def get_user(email: str) -> Optional[dict]:
    """Fetch user by email from mock store."""
    return user_store.get(email)

# PUBLIC_INTERFACE
def authenticate_user(email: str, password: str):
    """Authenticate user credentials."""
    user = get_user(email)
    if not user or not verify_password(password, user["hashed_password"]):
        return None
    return user

# PUBLIC_INTERFACE
def register_user(email: EmailStr, password: str) -> dict:
    """Register user, add to store, return user dict."""
    global user_id_counter
    if email in user_store:
        raise HTTPException(status_code=400, detail="Email already registered")
    user_dict = {"id": user_id_counter, "email": email, "hashed_password": get_password_hash(password)}
    user_store[email] = user_dict
    user_id_counter += 1
    return user_dict

# PUBLIC_INTERFACE
def get_current_user(token: str = Depends(oauth2_scheme)) -> UserOut:
    """Dependency for extracting current user from JWT."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not authenticate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: int = payload.get("user_id")
        email: str = payload.get("sub")
        if user_id is None or email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = user_store.get(email)
    if user is None or user["id"] != user_id:
        raise credentials_exception

    return UserOut(id=user["id"], email=user["email"])
