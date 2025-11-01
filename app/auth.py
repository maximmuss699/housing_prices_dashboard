import os
import logging
from datetime import datetime, timedelta, timezone
from typing import List, Optional, Tuple

import jwt
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer


# JWT authentication setup
_security = HTTPBearer(auto_error=False)
logger = logging.getLogger(__name__)


# Audit logging for authentication failures
def _audit_fail(req: Request, reason: str) -> None:
    client = req.client.host if req.client else "?"
    logger.warning(
        "auth_failure",
        extra={
            "reason": reason,
            "path": req.url.path,
            "client_ip": client,
            "method": req.method,
        },
    )


# Retrieve JWT secrets from environment variables
def _get_jwt_secrets() -> List[str]:
    secrets = os.getenv("JWT_SECRETS") or os.getenv("JWT_SECRET")
    if not secrets:
        return []
    return [s.strip() for s in secrets.split(",") if s.strip()]

# Common JWT parameters
def _jwt_common_params() -> Tuple[Optional[str], Optional[str], str]:
    issuer = os.getenv("JWT_ISSUER")
    audience = os.getenv("JWT_AUDIENCE")
    alg = os.getenv("JWT_ALG", "HS256")
    return issuer, audience, alg

# Verify JWT token against available secrets
def _verify_jwt(token: str) -> Optional[dict]:
    issuer, audience, alg = _jwt_common_params()
    options = {"require": ["exp", "iat"]}
    for secret in _get_jwt_secrets():
        try:
            payload = jwt.decode(
                token,
                secret,
                algorithms=[alg],
                audience=audience if audience else None,
                issuer=issuer if issuer else None,
                options=options,
            )
            return payload
        except jwt.PyJWTError:
            continue
    return None


# Issue a new JWT token for the given subject
def issue_jwt(subject: str) -> str:
    secrets = _get_jwt_secrets()
    if not secrets:
        raise RuntimeError("JWT_SECRETS (or JWT_SECRET) must be set to issue JWTs")
    issuer, audience, alg = _jwt_common_params()
    ttl = int(os.getenv("JWT_TTL_SECONDS", "900"))
    now = datetime.now(timezone.utc)
    payload = {
        "sub": subject,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(seconds=ttl)).timestamp()),
    }
    if issuer:
        payload["iss"] = issuer
    if audience:
        payload["aud"] = audience
    token = jwt.encode(payload, secrets[0], algorithm=alg)
    return token


# Dependency to require and validate bearer token
def require_token(request: Request, creds: HTTPAuthorizationCredentials = Depends(_security)) -> str:
    # Validate presence and scheme of credentials
    if not creds or creds.scheme.lower() != "bearer":
        _audit_fail(request, "missing_bearer")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "missing_bearer", "message": "Missing bearer token"},
        )

    # Validate JWT token
    raw = creds.credentials
    payload = _verify_jwt(raw)
    if not payload:
        _audit_fail(request, "invalid_jwt")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "invalid_token", "message": "Invalid token"},
        )
    subject = str(payload.get("sub", "anonymous"))
    # Attach to request state for downstream logging/usage
    try:
        request.state.user_id = subject
    except Exception:
        pass
    # Return a limiter key; rate limit per-user
    return f"user:{subject}"
