from pydantic import BaseModel, Field

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

