from fastapi import FastAPI, Response, Depends, HTTPException
from models import UserCreate, UserLogin
from database import users_collection
from auth import hash_password, verify_password, create_token
from deps import get_current_user
from fastapi.middleware.cors import CORSMiddleware
from product_routes import router as product_router
from fastapi.staticfiles import StaticFiles
from variant_routes import router as variant_router
from order_routes import router as order_router
from warehouse_routes import router as warehouse_router
from dashboard_routes import router as dashboard_router
from cart_routes import router as cart_router
from purchase_routes import router as purchase_router

app = FastAPI()

app.include_router(product_router)
app.include_router(variant_router)
app.include_router(order_router)
app.include_router(warehouse_router)
app.include_router(dashboard_router)
app.include_router(cart_router)
app.include_router(purchase_router)

app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[ "http://localhost:3000",
        "http://localhost:3001"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/signup")
async def signup(user: UserCreate):
    existing = await users_collection.find_one({"email": user.email})
    if existing:
        raise HTTPException(status_code=400, detail="User exists")

    user_dict = user.dict()
    user_dict["password"] = hash_password(user.password)

    await users_collection.insert_one(user_dict)

    return {"message": "User created"}



@app.post("/login")
async def login(data: UserLogin, response: Response):
    user = await users_collection.find_one({"email": data.email})

    if not user or not verify_password(data.password, user["password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_token({
        "email": user["email"],
        "role": user["role"],
        "name": user["name"]
    })

    response.set_cookie(
        key="token",
        value=token,
        httponly=True,
        samesite="lax",   
        secure=False
    )

    return {"message": "Login successful"}



@app.get("/me")
async def me(user=Depends(get_current_user)):
    return user



@app.post("/logout")
async def logout(response: Response):
    response.delete_cookie("token")
    return {"message": "Logged out"}


@app.get("/users")
async def get_users():
    users = await users_collection.find().to_list(100)

    for u in users:
        u["_id"] = str(u["_id"])   

    return users