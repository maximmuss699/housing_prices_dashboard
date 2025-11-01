import os
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware

from .auth import require_token, issue_jwt
from .model_runtime import runtime
from .rate_limit import FixedWindowLimiter, limiter_dependency_factory
from .schemas import PredictionInput, PredictionOutput, TokenRequest, TokenResponse

# Rate limiting configuration
RATE_LIMIT_MAX = int(os.getenv("RATE_LIMIT_MAX", "30"))
RATE_LIMIT_WINDOW = int(os.getenv("RATE_LIMIT_WINDOW", "60"))

# Initialize rate limiter
_limiter = FixedWindowLimiter(RATE_LIMIT_MAX, RATE_LIMIT_WINDOW)
limit_for = limiter_dependency_factory(_limiter)

app = FastAPI(title="Housing Price Predictor", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Health check endpoint
# Used by orchestration tools to verify service is running
@app.get("/health")
def health() -> dict:
    return {"status": "ok"}

# Testing endpoint to issue JWT tokens
# Requires client credentials via env vars
@app.post("/token", response_model=TokenResponse)
def token(req: TokenRequest) -> TokenResponse:
    # Minimal credential check via env vars
    cid = os.getenv("CLIENT_ID")
    csec = os.getenv("CLIENT_SECRET")
    if not cid or not csec or req.client_id != cid or req.client_secret != csec:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid client credentials")
    ttl = int(os.getenv("JWT_TTL_SECONDS", "900"))
    access_token = issue_jwt(subject=req.client_id)
    return TokenResponse(access_token=access_token, expires_in=ttl)

# Rate-limited dependency
# Applies rate limiting based on bearer token
def _rate_limit(token: str = Depends(require_token)):
    # Use the bearer token as the rate-limit key
    limit_for(token)


# Prediction endpoint
# Accepts input data and returns model predictions ( Needs bearer token )
@app.post("/predict", response_model=PredictionOutput)
def predict(
    payload: PredictionInput,
    _: None = Depends(_rate_limit),
):
    X = runtime.prepare_features(payload.dict())
    y = runtime.predict(X)
    return {"prediction": y}
