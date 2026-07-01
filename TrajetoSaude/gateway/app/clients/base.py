import httpx
from fastapi import HTTPException


class ServiceClient:
     def __init__(self, base_url: str, service_name: str):
          self.base_url = base_url.rstrip("/")
          self.service_name = service_name

     async def get(self, path: str, params: dict | None = None, headers: dict | None = None) -> dict:
          url = f"{self.base_url}{path}"
          try:
               async with httpx.AsyncClient(timeout=30.0) as client:
                    resp = await client.get(url, params=params, headers=headers or {})
          except httpx.RequestError as exc:
               raise HTTPException(
                    status_code=503,
                    detail=f"MS {self.service_name} indisponível: {exc}",
               ) from exc

          if resp.status_code >= 400:
               raise HTTPException(status_code=resp.status_code, detail=resp.text)
          return resp.json()

     async def patch(self, path: str, json: dict | None = None, headers: dict | None = None, params: dict | None = None) -> dict:
          url = f"{self.base_url}{path}"
          try:
               async with httpx.AsyncClient(timeout=30.0) as client:
                    resp = await client.patch(url, json=json, headers=headers or {}, params=params or {})
          except httpx.RequestError as exc:
               raise HTTPException(
                    status_code=503,
                    detail=f"MS {self.service_name} indisponível: {exc}",
               ) from exc
          if resp.status_code >= 400:
               raise HTTPException(status_code=resp.status_code, detail=resp.text)
          return resp.json()

     async def post(
          self,
          path: str,
          json: dict | None = None,
          headers: dict | None = None,
          timeout: float = 60.0,
     ) -> dict:
          url = f"{self.base_url}{path}"
          try:
               async with httpx.AsyncClient(timeout=timeout) as client:
                    resp = await client.post(url, json=json, headers=headers or {})
          except httpx.RequestError as exc:
               raise HTTPException(
                    status_code=503,
                    detail=f"MS {self.service_name} indisponível: {exc}",
               ) from exc

          if resp.status_code >= 400:
               raise HTTPException(status_code=resp.status_code, detail=resp.text)
          return resp.json()

     async def health(self) -> dict:
          return await self.get("/health")
