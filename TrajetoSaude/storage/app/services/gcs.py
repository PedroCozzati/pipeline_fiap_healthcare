import re

from google.api_core.exceptions import Forbidden, NotFound
from google.cloud import storage

from app.config import settings

_GS_URI_PATTERN = re.compile(r"^gs://([^/]+)/?(.*)$")


def get_gcs_client() -> storage.Client:
     return storage.Client(project=settings.gcp_project_id)


def parse_gcs_uri(uri: str) -> tuple[str, str]:
     match = _GS_URI_PATTERN.match(uri.strip())
     if not match:
          raise ValueError(f"URI GCS inválida: {uri}")
     return match.group(1), match.group(2)


def resolve_list_target(prefix: str = "") -> tuple[str, str]:
     """Resolve bucket e prefixo de objeto para listagem."""
     prefix = prefix.strip()

     if prefix.startswith("gs://"):
          return parse_gcs_uri(prefix)

     bucket = settings.gcs_bucket_name
     base = settings.gcs_artifacts_prefix.strip("/")

     if prefix:
          object_prefix = f"{base}/{prefix.lstrip('/')}" if base else prefix.lstrip("/")
     else:
          object_prefix = base

     return bucket, object_prefix


def _ensure_bucket_exists(client: storage.Client, bucket_name: str) -> storage.Bucket:
     bucket = client.bucket(bucket_name)
     try:
          if not bucket.exists():
               raise FileNotFoundError(
                    f"Bucket não encontrado: gs://{bucket_name}. "
                    f"Ajuste GCS_BUCKET_NAME no .env (valor atual: {settings.gcs_bucket_name!r})."
               )
     except Forbidden as exc:
          raise PermissionError(
               f"Sem permissão para acessar gs://{bucket_name}. "
               f"Verifique roles da service account (ex.: Storage Object Viewer)."
          ) from exc
     return bucket


def list_blobs(prefix: str = "") -> dict:
     bucket_name, object_prefix = resolve_list_target(prefix)
     client = get_gcs_client()
     bucket = _ensure_bucket_exists(client, bucket_name)

     try:
          items = [
               {
                    "name": blob.name,
                    "size_bytes": blob.size,
                    "updated": blob.updated.isoformat() if blob.updated else None,
                    "content_type": blob.content_type,
               }
               for blob in bucket.list_blobs(prefix=object_prefix or None)
          ]
     except NotFound as exc:
          raise FileNotFoundError(f"Prefixo não encontrado: gs://{bucket_name}/{object_prefix}") from exc

     return {
          "bucket": bucket_name,
          "prefix": object_prefix,
          "objects": items,
          "count": len(items),
     }


def download_blob_text(blob_name: str) -> dict:
     if blob_name.startswith("gs://"):
          bucket_name, blob_name = parse_gcs_uri(blob_name)
     else:
          bucket_name = settings.gcs_bucket_name

     client = get_gcs_client()
     bucket = _ensure_bucket_exists(client, bucket_name)
     blob = bucket.blob(blob_name)

     if not blob.exists():
          raise FileNotFoundError(f"Objeto não encontrado: gs://{bucket_name}/{blob_name}")

     content = blob.download_as_text(encoding="utf-8")
     return {
          "bucket": bucket_name,
          "name": blob_name,
          "content": content,
     }


def upload_blob_text(blob_name: str, content: str, content_type: str = "text/plain") -> dict:
     if blob_name.startswith("gs://"):
          bucket_name, blob_name = parse_gcs_uri(blob_name)
     else:
          bucket_name = settings.gcs_bucket_name

     client = get_gcs_client()
     bucket = _ensure_bucket_exists(client, bucket_name)
     blob = bucket.blob(blob_name)
     blob.upload_from_string(content, content_type=content_type)

     return {
          "bucket": bucket_name,
          "name": blob_name,
          "status": "uploaded",
     }
