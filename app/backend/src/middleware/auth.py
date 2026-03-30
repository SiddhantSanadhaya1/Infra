import os
import logging
from typing import Optional

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt

logger = logging.getLogger(__name__)

SECRET_KEY = os.getenv("JWT_SECRET_KEY", "insureco-secret-key-for-dev-only")
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
DEV_TOKEN = "insureco-demo-token"

security = HTTPBearer(auto_error=False)


def decode_jwt(token: str) -> Optional[dict]:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError as exc:
        logger.debug("JWT decode error: %s", exc)
        return None


async def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> dict:
    """
    Validate Bearer token. For demo purposes, the hardcoded token 'insureco-demo-token'
    bypasses JWT validation and is treated as a demo policyholder.
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header missing",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials

    # Demo bypass token
    if token == DEV_TOKEN:
        demo_user = {
            "policyholder_id": "00000000-0000-0000-0000-000000000001",
            "email": "demo@insureco.com",
            "role": "demo",
        }
        request.state.policyholder_id = demo_user["policyholder_id"]
        return demo_user

    payload = decode_jwt(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    policyholder_id = payload.get("sub")
    if not policyholder_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token missing subject claim",
            headers={"WWW-Authenticate": "Bearer"},
        )

    request.state.policyholder_id = policyholder_id
    return {
        "policyholder_id": policyholder_id,
        "email": payload.get("email"),
        "role": payload.get("role", "policyholder"),
    }


async def optional_auth(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> Optional[dict]:
    """Non-enforcing version for routes that work with or without auth."""
    if credentials is None:
        return None
    try:
        return await get_current_user(request, credentials)
    except HTTPException:
        return None
