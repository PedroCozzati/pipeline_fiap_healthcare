import httpx

from app.config import settings


class StorageServiceClient:
     def __init__(self, base_url: str | None = None):
          self.base_url = (base_url or settings.storage_service_url).rstrip("/")

     def upload_text(self, blob_name: str, content: str, content_type: str = "text/plain") -> dict:
          return self._upload(blob_name, content, content_type, encoding="utf-8")

     def upload_base64(self, blob_name: str, content: str, content_type: str = "application/octet-stream") -> dict:
          return self._upload(blob_name, content, content_type, encoding="base64")

     def _upload(self, blob_name: str, content: str, content_type: str, encoding: str) -> dict:
          payload = {
               "blob_name": blob_name,
               "content": content,
               "content_type": content_type,
               "encoding": encoding,
          }
          url = f"{self.base_url}/storage/gcs/upload"
          try:
               with httpx.Client(timeout=120.0) as client:
                    response = client.post(url, json=payload)
          except httpx.RequestError as exc:
               raise RuntimeError(f"MS storage indisponível: {exc}") from exc

          if response.status_code >= 400:
               raise RuntimeError(f"Falha no upload GCS ({response.status_code}): {response.text}")
          return response.json()
