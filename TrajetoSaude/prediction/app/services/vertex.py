import httpx
import google.auth
import google.auth.transport.requests

from app.config import settings


def get_access_token() -> str:
     credentials, _ = google.auth.default(
          scopes=["https://www.googleapis.com/auth/cloud-platform"]
     )
     request = google.auth.transport.requests.Request()
     if not credentials.valid:
          credentials.refresh(request)
     return credentials.token


async def query_vertex(payload: dict) -> dict:
     if not settings.gcp_reasoning_engine_url:
          raise RuntimeError("GCP_REASONING_ENGINE_URL não configurada.")

     token = get_access_token()
     async with httpx.AsyncClient(timeout=60.0) as client:
          resp = await client.post(
               settings.gcp_reasoning_engine_url,
               json=payload,
               headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json",
               },
          )

     if resp.status_code != 200:
          raise RuntimeError(f"Vertex AI retornou {resp.status_code}: {resp.text}")

     return resp.json()
