from typing import Any, Dict
from pydantic import BaseModel, Field, EmailStr

# Pydantic schema for input data validation
class PredictionInput(BaseModel):
    longitude: float = Field(...)
    latitude: float = Field(...)
    housing_median_age: float = Field(...)
    total_rooms: float = Field(...)
    total_bedrooms: float = Field(...)
    population: float = Field(...)
    households: float = Field(...)
    median_income: float = Field(...)
    ocean_proximity: str = Field(..., description="Category like 'NEAR OCEAN', 'INLAND', '<1H OCEAN', 'ISLAND', 'NEAR BAY'")

# Pydantic schema for output data validation
class PredictionOutput(BaseModel):
    prediction: float


class TokenRequest(BaseModel):
    client_id: str
    client_secret: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


# Pydantic schema for user creation and output
# ! min length password == 6
class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(
        ..., min_length=8, description="Password at least 8 characters"
    )


class UserOut(BaseModel):
    id: int
    email: EmailStr


class PredictionRecord(BaseModel):
    id: int
    predicted_value: float
    payload: Dict[str, Any]
    created_at: str
