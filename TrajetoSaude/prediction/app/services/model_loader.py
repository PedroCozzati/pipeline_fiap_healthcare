import tempfile
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

     from app.config import SERVICE_ROOT
     client = storage.Client(project=settings.gcp_project_id)
     bucket = client.bucket(bucket_name)
     blob = bucket.blob(blob_name)
     local_path = SERVICE_ROOT / "artefatos" / Path(blob_name).name
     local_path.parent.mkdir(parents=True, exist_ok=True)
     blob.download_to_filename(str(local_path))
     return joblib.load(local_path)


def load_model():
     source = settings.model_source.lower()
     if source == "gcs":
          try:
               return load_from_gcs(settings.model_gcs_uri)
          except Exception as exc:
               print(f"Falha ao carregar modelo de GCS: {exc}")
               print("Tentando carregar modelo local...")
               return load_from_local(resolve_model_path())

     if source == "local":
          return load_from_local(resolve_model_path())

     raise ValueError(f"Fonte de modelo desconhecida: {settings.model_source}")


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
