import os
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer


_security = HTTPBearer(auto_error=False)


def require_token(creds: HTTPAuthorizationCredentials = Depends(_security)) -> str:
    expected = os.getenv("API_TOKEN", "test_token228")
    if not creds or creds.scheme.lower() != "bearer":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token")
    if creds.credentials != expected:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    return creds.credentials

