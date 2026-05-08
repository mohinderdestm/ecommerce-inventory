from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from app.api.v1 import websocket
from app.api.v1.api import api_router
from app.core.kafka import kafka_manager
from app.services.kafka_event_handler import KafkaEventHandler


@asynccontextmanager
async def lifespan(_: FastAPI):
    kafka_manager.set_message_handler(KafkaEventHandler.handle)
    await kafka_manager.start()
    try:
        yield
    finally:
        await kafka_manager.stop()


app = FastAPI(lifespan=lifespan)


app.mount("/static", StaticFiles(directory="app/static"), name="static")

app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")
templates = Jinja2Templates(directory="app/templates")

app.include_router(websocket.router)
app.include_router(api_router, prefix="/api/v1")


@app.get("/", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse(request, "login.html", {"request": request})


@app.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    return templates.TemplateResponse(request, "register.html", {"request": request})


@app.get("/home", response_class=HTMLResponse)
async def home_page(request: Request):
    return templates.TemplateResponse(request, "home.html", {"request": request})


@app.get("/register-supplier", response_class=HTMLResponse)
async def register_supplier_page(request: Request):
    return templates.TemplateResponse(
        request, "register_supplier.html", {"request": request}
    )
