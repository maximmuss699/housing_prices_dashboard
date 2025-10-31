from pathlib import Path
from typing import List

import joblib
import pandas as pd

# paths
ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "housing.csv"
MODEL_PATH = ROOT / "model.joblib"


class ModelRuntime:
    def __init__(self) -> None:
        self.expected_columns: List[str] = self._compute_expected_columns()
        self.model = self._load_model()

    # Compute expected feature columns from training data
    def _compute_expected_columns(self) -> List[str]:
        df = pd.read_csv(DATA_PATH)
        df = df.dropna()
        df = pd.get_dummies(df)
        features = df.drop(["median_house_value"], axis=1)
        return list(features.columns)

    def _load_model(self):
        return joblib.load(MODEL_PATH)

    def prepare_features(self, payload: dict) -> pd.DataFrame:
        # Convert single record to DataFrame and align with training columns
        df = pd.DataFrame([payload])
        df = pd.get_dummies(df)
        # Align to expected columns
        aligned = df.reindex(columns=self.expected_columns, fill_value=0)
        return aligned

    def predict(self, X: pd.DataFrame) -> float:
        y = self.model.predict(X)
        return float(y[0])


# Singleton runtime for the app
runtime = ModelRuntime()

