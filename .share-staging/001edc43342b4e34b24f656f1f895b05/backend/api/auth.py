from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import jwt, time, bcrypt
from config.settings import settings

router = APIRouter(prefix="/api/auth", tags=["auth"])

class LoginReq(BaseModel):
    username: str
    password: str

# pre-hash admin password for check (if bcrypt available)
# For MVP allow plain compare as well

@router.post("/login")
def login(req: LoginReq):
    if req.username != settings.ADMIN_USERNAME:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    # Allow plain or bcrypt
    if req.password != settings.ADMIN_PASSWORD:
        # try bcrypt if settings stores hashed? fallback reject
        raise HTTPException(status_code=401, detail="Invalid credentials")
    payload = {
        "sub": req.username,
        "role": "admin",
        "exp": int(time.time()) + settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        "iat": int(time.time())
    }
    token = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return {"access_token": token, "token_type": "bearer"}

def verify_token(token: str):
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")
