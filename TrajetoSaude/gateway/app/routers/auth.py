from fastapi import APIRouter, Request

from app.clients.services import auth_client

router = APIRouter()


@router.post("/register")
async def register(request: Request):
    return await auth_client.post("/auth/register", json=await request.json())


@router.post("/login")
async def login(request: Request):
    return await auth_client.post("/auth/login", json=await request.json())


@router.get("/me")
async def me(request: Request):
    auth_header = request.headers.get("Authorization", "")
    return await auth_client.get("/auth/me", headers={"Authorization": auth_header})


@router.post("/verify")
async def verify(request: Request):
    auth_header = request.headers.get("Authorization", "")
    return await auth_client.post("/auth/verify", headers={"Authorization": auth_header})


@router.post("/validate-coren")
async def validate_coren(request: Request):
    return await auth_client.post("/auth/validate-coren", json=await request.json())
