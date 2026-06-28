from pathlib import Path
from typing import Dict, Optional, List

import joblib
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split


DEFAULT_FEATURE_COLUMNS = [
    "Idade",
    "Tempo_Deslocamento_Min",
    "Qtd_UBS_Origem_3km",
    "Glicemia_Aferida",
]
DEFAULT_TARGET_COLUMN = "Risco_Evasao"


def train_risk_model(
    df: pd.DataFrame,
    feature_columns: Optional[List[str]] = None,
    target_column: str = DEFAULT_TARGET_COLUMN,
    test_size: float = 0.2,
    random_state: int = 42,
):
    """Train a logistic regression risk model from a labeled DataFrame."""
    feature_columns = feature_columns or DEFAULT_FEATURE_COLUMNS
    if target_column not in df.columns:
        raise ValueError(f"Target column {target_column} not found in DataFrame.")

    X = df[feature_columns].astype(float)
    y = df[target_column].astype(int)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=random_state
    )

    model = LogisticRegression(max_iter=1000)
    model.fit(X_train, y_train)

    return model, X_test, y_test


def save_model(model, path: Path):
    """Save a trained model to disk using Joblib."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, path)
    return path


def load_model(path: Path):
    """Load a persisted model from disk."""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Model file not found: {path}")
    return joblib.load(path)


def predict_risk(model, payload: Dict[str, float]):
    """Predict risk probability for a single observation."""
    values = [payload.get(column, 0.0) for column in DEFAULT_FEATURE_COLUMNS]
    array = np.array(values, dtype=float).reshape(1, -1)
    score = model.predict_proba(array)[0][1]
    label = int(model.predict(array)[0])
    return {"risk_probability": float(score), "risk_label": label, "risk_label_texto": "ALTO RISCO" if label==1 else "BAIXO RISCO"}


def generate_demo_training_data(n_samples: int = 1000) -> pd.DataFrame:
    """Generate a synthetic demo dataset if no labeled training file exists."""
    rng = np.random.default_rng(42)
    df = pd.DataFrame({
        "Idade": rng.integers(18, 80, size=n_samples),
        "Tempo_Deslocamento_Min": rng.integers(10, 180, size=n_samples),
        "Qtd_UBS_Origem_3km": rng.integers(0, 10, size=n_samples),
        "Glicemia_Aferida": rng.integers(80, 260, size=n_samples),
    })
    df[DEFAULT_TARGET_COLUMN] = np.where(
        (df["Tempo_Deslocamento_Min"] > 90) & (df["Qtd_UBS_Origem_3km"] < 3)
        | (df["Glicemia_Aferida"] > 100),
        1,
        0,
    )
    return df
