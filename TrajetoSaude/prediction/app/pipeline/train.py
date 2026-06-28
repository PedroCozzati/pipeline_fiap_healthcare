from pathlib import Path
from typing import Optional

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


def generate_demo_training_data(n_samples: int = 1000) -> pd.DataFrame:
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


def train_risk_model(
     df: pd.DataFrame,
     feature_columns: Optional[list[str]] = None,
     target_column: str = DEFAULT_TARGET_COLUMN,
     test_size: float = 0.2,
     random_state: int = 42,
):
     feature_columns = feature_columns or DEFAULT_FEATURE_COLUMNS
     if target_column not in df.columns:
          raise ValueError(f"Coluna alvo {target_column} não encontrada no DataFrame.")

     x = df[feature_columns].astype(float)
     y = df[target_column].astype(int)

     x_train, x_test, y_train, y_test = train_test_split(
          x, y, test_size=test_size, random_state=random_state
     )

     model = LogisticRegression(max_iter=1000)
     model.fit(x_train, y_train)
     accuracy = float(model.score(x_test, y_test))
     return model, accuracy


def resolve_training_data(output_dir: Path) -> tuple[pd.DataFrame, str]:
     training_csv = output_dir / "risk_training.csv"
     if training_csv.exists():
          return pd.read_csv(training_csv), f"arquivo existente: {training_csv.name}"

     demo = generate_demo_training_data()
     return demo, "dataset sintético de demonstração"
