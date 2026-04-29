from fastapi import HTTPException, Security, status, Depends
from fastapi.security.api_key import APIKeyHeader
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.core.config import settings
import jwt
from typing import Optional

api_key_header = APIKeyHeader(name=settings.API_KEY_NAME, auto_error=False)
security_bearer = HTTPBearer(auto_error=False)

async def get_api_key(
    api_key_header: str = Security(api_key_header),
):
    if api_key_header == settings.API_KEY:
        return api_key_header
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Could not validate API Key",
    )

def decode_jwt_token(token: str) -> dict:
    """
    Decode and verify JWT token based on Node.js implementation.
    """
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM],
            issuer=settings.JWT_ISSUER,
            audience=settings.JWT_AUDIENCE
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
        )
    except jwt.InvalidTokenError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {str(e)}",
        )

async def get_current_username(
    auth: Optional[HTTPAuthorizationCredentials] = Depends(security_bearer)
) -> str:
    """
    Dependency to get the current username from JWT token.
    Matches Node.js logic: decoded.user?.username
    """
    if not auth:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header missing",
        )
    
    payload = decode_jwt_token(auth.credentials)
    
    # Access nested token structure: decoded.user.username
    user_data = payload.get("user", {})
    username = user_data.get("username")
    
    if not username:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token structure: username not found",
        )
        
    return username
