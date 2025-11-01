# Main API application for Housing Price Predictor
# Implements user authentication, rate limiting, and prediction endpoints.
#
#
import os
import logging
import uuid
from typing import Any, List
from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from fastapi.openapi.utils import get_openapi
from fastapi.middleware.cors import CORSMiddleware

from .auth import require_token, issue_jwt
from .model_runtime import runtime
from .rate_limit import FixedWindowLimiter, limiter_dependency_factory
from .schemas import (
    PredictionInput,
    PredictionOutput,
    TokenResponse,
    UserCreate,
    UserOut,
)
from .db import get_db, init_db
from .crud import create_user, get_user_by_email, verify_password, list_users
from sqlalchemy.orm import Session

# Rate limiting configuration
RATE_LIMIT_MAX = int(os.getenv("RATE_LIMIT_MAX", "30"))
RATE_LIMIT_WINDOW = int(os.getenv("RATE_LIMIT_WINDOW", "60"))

# Initialize rate limiter
_limiter = FixedWindowLimiter(RATE_LIMIT_MAX, RATE_LIMIT_WINDOW)
limit_for = limiter_dependency_factory(_limiter)

# Just some metadata for OpenAPI docs
tags_metadata = [
    {"name": "Auth", "description": "User registration and login"},
    {"name": "Predictions", "description": "Endpoints for price predictions"},
    {"name": "Health", "description": "Service health checks"},
]

app = FastAPI(title="Housing Price Predictor", version="1.0.0", openapi_tags=tags_metadata)
log_app = logging.getLogger("app.api")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Custom OpenAPI schema generation to include security schemes
@app.on_event("startup")
def on_startup() -> None:
    init_db()


# Health "Debug" check endpoint
# Used by orchestration tools to verify service is running
@app.get("/health", tags=["Health"], openapi_extra={"security": []})
def health() -> dict:
    return {"status": "ok"}


# Request logging middleware with request ID
@app.middleware("http")
async def log_requests(request: Request, call_next):
    req_id = request.headers.get("X-Request-ID") or uuid.uuid4().hex[:12]
    request.state.request_id = req_id
    log_app.info(
        "request_start",
        extra={"id": req_id, "method": request.method, "path": request.url.path},
    )
    try:
        response = await call_next(request)
        log_app.info(
            "request_end",
            extra={"id": req_id, "status": response.status_code},
        )
        response.headers["X-Request-ID"] = req_id
        return response
    except Exception:
        log_app.exception("request_exception", extra={"id": req_id})
        return JSONResponse(
            status_code=500,
            content={"code": "internal_error", "message": "Unexpected server error"},
            headers={"X-Request-ID": req_id},
        )


# Global error handlers for better diagnostics
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    req_id = getattr(request.state, "request_id", None) or uuid.uuid4().hex[:12]
    log_app.info(
        "validation_error",
        extra={"id": req_id, "errors": exc.errors(), "path": request.url.path},
    )
    return JSONResponse(
        status_code=422,
        content={"code": "validation_error", "message": "Invalid request", "errors": exc.errors()},
        headers={"X-Request-ID": req_id},
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    req_id = getattr(request.state, "request_id", None) or uuid.uuid4().hex[:12]
    log_app.info(
        "http_error",
        extra={"id": req_id, "status": exc.status_code, "detail": exc.detail},
    )
    # Ensure detail is dict with code/message for consistency
    if isinstance(exc.detail, dict):
        content: Any = exc.detail
    else:
        content = {"code": "http_error", "message": str(exc.detail)}
    return JSONResponse(status_code=exc.status_code, content=content, headers={"X-Request-ID": req_id})

# Testing endpoint to issue JWT tokens
# Requires client credentials via env vars
# Removed public token issuance endpoint. Only application login issues JWTs.


# Create user (signup)
@app.post("/users", response_model=UserOut, status_code=201, tags=["Auth"], openapi_extra={"security": []})
def create_user_endpoint(payload: UserCreate, db: Session = Depends(get_db)) -> UserOut:
    existing = get_user_by_email(db, payload.email)
    if existing:
        log_app.info("signup_conflict", extra={"email": payload.email})
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"code": "user_exists", "message": "Email already registered"},
        )
    user = create_user(db, payload.email, payload.password)
    log_app.info("signup_success", extra={"user_id": user.id, "email": user.email})
    return UserOut(id=user.id, email=user.email)


# Login user -> issue JWT
@app.post("/login", response_model=TokenResponse, tags=["Auth"], openapi_extra={"security": []})
def login(payload: UserCreate, db: Session = Depends(get_db)) -> TokenResponse:
    user = get_user_by_email(db, payload.email)
    if not user or not verify_password(payload.password, user.password_hash):
        log_app.info("login_failed", extra={"email": payload.email})
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "invalid_credentials", "message": "Invalid email or password"},
        )
    ttl = int(os.getenv("JWT_TTL_SECONDS", "900"))
    token = issue_jwt(subject=str(user.id))
    log_app.info("login_success", extra={"user_id": user.id})
    return TokenResponse(access_token=token, expires_in=ttl)


# List users (requires auth)
@app.get("/users", response_model=List[UserOut], tags=["Auth"])
def list_users_endpoint(
    request: Request,
    offset: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    _: str = Depends(require_token),
) -> List[UserOut]:
    users = list_users(db, offset=offset, limit=limit)
    log_app.info(
        "users_list",
        extra={
            "actor": getattr(request.state, "user_id", None),
            "offset": offset,
            "limit": limit,
            "count": len(users),
        },
    )
    return [UserOut(id=u.id, email=u.email) for u in users]

# Rate-limited dependency
# Applies rate limiting based on bearer token
def _rate_limit(token: str = Depends(require_token)):
    # Use the bearer token as the rate-limit key
    limit_for(token)


# Prediction endpoint
# Accepts input data and returns model predictions ( Needs bearer token )
@app.post("/predict", response_model=PredictionOutput, tags=["Predictions"])
def predict(
    payload: PredictionInput,
    _: None = Depends(_rate_limit),
):
    try:
        X = runtime.prepare_features(payload.dict())
        y = runtime.predict(X)
        return {"prediction": y}
    except Exception:
        log_app.exception("predict_failed")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "prediction_error", "message": "Failed to compute prediction"},
        )


