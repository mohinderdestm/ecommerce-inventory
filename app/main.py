from fastapi import FastAPI
from app.routes.auth import router as auth_router
from app.routes.products import router as product_router 
from fastapi.middleware.cors import CORSMiddleware
import app.core.cloudinary_config

app = FastAPI(title="Ecommerce Inventory System")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:5500",
        "http://localhost:5500"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(product_router) 


@app.get("/")
async def root():
    return {"message": "Server Running"}