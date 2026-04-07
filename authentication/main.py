from fastapi import FastAPI, Depends, Request
from routes import router as Auth_router
from fastapi.templating import Jinja2Templates
from utils import security

app = FastAPI(title="Auth Service")

app.include_router(Auth_router)

templates = Jinja2Templates(directory="templates")


@app.get("/")
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/signup-ui")
async def signup_ui(request: Request):
    return templates.TemplateResponse("signup.html", {"request": request})


@app.get("/login-ui")
async def login_ui(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@app.get("/dashboard")
async def dashboard(request: Request, user=Depends(security.get_current_user)):
    return templates.TemplateResponse(
        "dashboard.html",
        {"request": request, "user": user}
    )