from pathlib import Path

import joblib
import numpy as np
from google.cloud import storage

from app.config import settings, resolve_model_path

DEFAULT_FEATURE_COLUMNS = [
     "Idade",
     "Tempo_Deslocamento_Min",
     "Qtd_UBS_Origem_3km",
     "Glicemia_Aferida",
]


def load_from_local(path: str | Path):
     path = Path(path)
     if not path.exists():
          raise FileNotFoundError(f"Modelo local não encontrado: {path}")
     return joblib.load(path)


def load_from_gcs(gcs_uri: str):
     if not gcs_uri.startswith("gs://"):
          raise ValueError(f"URI GCS inválida: {gcs_uri}")

     _, _, bucket_name, *blob_parts = gcs_uri.split("/")
     blob_name = "/".join(blob_parts)

     client = storage.Client(project=settings.gcp_project_id)
     bucket = client.bucket(bucket_name)
     blob = bucket.blob(blob_name)

     local_path = Path("/tmp") / Path(blob_name).name
     blob.download_to_filename(str(local_path))
     return joblib.load(local_path)


def load_model():
     source = settings.model_source.lower()
     if source == "gcs":
          return load_from_gcs(settings.model_gcs_uri)
     return load_from_local(resolve_model_path())


def predict_risk(model, payload: dict) -> dict:
     values = [float(payload.get(column, 0.0)) for column in DEFAULT_FEATURE_COLUMNS]
     array = np.array(values, dtype=float).reshape(1, -1)
     score = float(model.predict_proba(array)[0][1])
     label = int(model.predict(array)[0])
     return {
          "risk_probability": score,
          "risk_label": label,
          "risk_label_texto": "ALTO RISCO" if label == 1 else "BAIXO RISCO",
          "features_usadas": dict(zip(DEFAULT_FEATURE_COLUMNS, values)),
     }
