import os

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path


# Import routers
from app.api.v1.routes.auth import router as auth_router
from app.api.v1.routes.products import router as product_router
from app.api.v1.routes.category import router as category_router
from app.api.v1.routes.suppliers import router as supplier_router

app = FastAPI(title="Inventory Management System")

# -------------------------------
#  CORS (for development)
# -------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------------------
#  API ROUTES
# -------------------------------
app.include_router(auth_router)


app.include_router(product_router)

app.include_router(category_router)
app.include_router(supplier_router)

# -------------------------------
#  FRONTEND SETUP
# -------------------------------

BASE_DIR = Path(__file__).resolve().parent

FRONTEND_DIR = BASE_DIR / "frontend"

# ✅ Create directories if they don't exist
os.makedirs("static/uploads/products", exist_ok=True)
os.makedirs("static/uploads/categories", exist_ok=True)

# Serve static files (CSS, JS)
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")

app.mount("/css", StaticFiles(directory=FRONTEND_DIR / "css"), name="css")
app.mount("/js", StaticFiles(directory=FRONTEND_DIR / "js"), name="js")

# -------------------------------
#  HTML ROUTES
# -------------------------------

# Login page
@app.get("/")
async def serve_login():
    return FileResponse(FRONTEND_DIR / "index.html")


# Dashboard page
@app.get("/dashboard")
async def serve_dashboard():
    return FileResponse(FRONTEND_DIR / "dashboard.html")

@app.get("/index.html")
async def serve_index_html():
    return FileResponse(FRONTEND_DIR / "index.html")

# -------------------------------
#  HEALTH CHECK (optional)
# -------------------------------
@app.get("/health")
async def health_check():
    return {"status": "OK"}