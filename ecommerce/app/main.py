from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os

from app.core.config import settings
from app.core.database import connect_to_mongo, close_mongo_connection
from app.core.log_config import setup_logging
from app.core.context import request_ip_ctx
from app.api.v1.routes import auth, users, products, categories, suppliers, variants, warehouses, sales_orders, inventory_movements, purchase_orders, reports, audit_logs
from fastapi import Request

setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    await connect_to_mongo()
    yield
    await close_mongo_connection()


app = FastAPI(
    title=settings.APP_TITLE,
    version=settings.APP_VERSION,
    description=(
        "Smart Inventory & Order Management Platform.\n\n"
        "Supports roles: **Admin**, **Customer**, **Supplier**."
    ),
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

import socket

def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('10.255.255.255', 1))
        IP = s.getsockname()[0]
        s.close()
        return IP
    except Exception:
        return '127.0.0.1'

@app.middleware("http")
async def add_ip_to_context(request: Request, call_next):
    x_forwarded_for = request.headers.get("x-forwarded-for")
    if x_forwarded_for:
        client_ip = x_forwarded_for.split(",")[0].strip()
    else:
        client_ip = request.headers.get("x-real-ip")
        if not client_ip:
            client_ip = request.client.host if request.client else None
            
    if client_ip in ("127.0.0.1", "::1", "localhost"):
        client_ip = get_local_ip()
        
    token = request_ip_ctx.set(client_ip)
    try:
        response = await call_next(request)
        return response
    finally:
        request_ip_ctx.reset(token)

# API Routes 
app.include_router(auth.router, prefix="/api/v1")
app.include_router(users.router, prefix="/api/v1")
app.include_router(categories.router, prefix="/api/v1")
app.include_router(products.router, prefix="/api/v1")
app.include_router(suppliers.router, prefix="/api/v1")
app.include_router(variants.router,    prefix="/api/v1")
app.include_router(warehouses.router, prefix="/api/v1")
app.include_router(sales_orders.router, prefix="/api/v1")
app.include_router(inventory_movements.router, prefix="/api/v1")
app.include_router(purchase_orders.router, prefix="/api/v1")
app.include_router(reports.router, prefix="/api/v1")
app.include_router(audit_logs.router, prefix="/api/v1")

# Static UI 
static_dir = os.path.join(os.path.dirname(__file__), "..", "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

    @app.get("/", include_in_schema=False)
    async def serve_ui():
        return FileResponse(os.path.join(static_dir, "index.html"))


@app.get("/health", tags=["Health"])
async def health():
    return {"status": "ok", "service": settings.APP_TITLE, "version": settings.APP_VERSION}
