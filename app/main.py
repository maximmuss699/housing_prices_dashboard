import os
from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .auth import require_token
from .model_runtime import runtime
from .rate_limit import FixedWindowLimiter, limiter_dependency_factory
from .schemas import PredictionInput, PredictionOutput

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
