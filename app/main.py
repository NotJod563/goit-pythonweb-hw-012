import asyncio
import redis.asyncio as redis
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from fastapi_limiter import FastAPILimiter

import cloudinary

from app.config import settings
from app.auth import router as auth_router
from app.users import router as users_router

contacts_router = None
try:
    from app.contacts import router as contacts_router
except ModuleNotFoundError:
    try:
        from app.routers.contacts import router as contacts_router
    except ModuleNotFoundError:
        contacts_router = None  

app = FastAPI(title="Contacts API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],        
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup():
    cloudinary.config(cloudinary_url=settings.CLOUDINARY_URL)

    for _ in range(10):
        try:
            r = await redis.from_url(
                settings.REDIS_URL, encoding="utf-8", decode_responses=True
            )
            await FastAPILimiter.init(r)
            break
        except Exception:
            await asyncio.sleep(1)

app.include_router(auth_router)
app.include_router(users_router)
if contacts_router:
    app.include_router(contacts_router)


app.openapi_schema = None

PUBLIC_PATHS = {
    ("/auth/signup", "post"),
    ("/auth/login", "post"),
    ("/auth/verify", "get"),
}

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description="API for managing contacts with authentication",
        routes=app.routes,
    )
    openapi_schema.setdefault("components", {}).setdefault("securitySchemes", {})["BearerAuth"] = {
        "type": "http",
        "scheme": "bearer",
        "bearerFormat": "JWT",
    }
    for path, methods in openapi_schema.get("paths", {}).items():
        for method_name, method in methods.items():
            if (path, method_name.lower()) in PUBLIC_PATHS:
                continue
            method.setdefault("security", [{"BearerAuth": []}])

    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi