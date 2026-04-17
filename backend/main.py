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



app = FastAPI()

app.include_router(product_router)
app.include_router(variant_router)
app.include_router(order_router)
app.include_router(warehouse_router)

app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ SIGNUP
@app.post("/signup")
async def signup(user: UserCreate):
    existing = await users_collection.find_one({"email": user.email})
    if existing:
        raise HTTPException(status_code=400, detail="User exists")

    user_dict = user.dict()
    user_dict["password"] = hash_password(user.password)

    await users_collection.insert_one(user_dict)

    return {"message": "User created"}


# ✅ LOGIN
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
        samesite="lax",   # ✅ IMPORTANT
        secure=False
    )

    return {"message": "Login successful"}


# ✅ CURRENT USER
@app.get("/me")
async def me(user=Depends(get_current_user)):
    return user


# ✅ LOGOUT
@app.post("/logout")
async def logout(response: Response):
    response.delete_cookie("token")
    return {"message": "Logged out"}

@app.get("/users")
async def get_users():
    users = await users_collection.find().to_list(100)

    for u in users:
        u["_id"] = str(u["_id"])   # ✅ CRITICAL FIX

    return users

# @app.get("/users")
# async def get_users():
#     data = await users_collection.find().to_list(100)

#     for d in data:
#         d["id"] = str(d["_id"])
#         del d["_id"]

#     return data


# @app.get("/users")
# async def get_users(supplier: bool = False):
#     if supplier:
#         data = await users_collection.find({"role": "supplier"}).to_list(100)

#         for d in data:
#             d["id"] = str(d["_id"])
#             del d["_id"]

#         return data

#     return []

# ✅ ROLE BASED ROUTES

# @app.get("/admin")
# async def admin(user=Depends(role_required(["admin"]))):
#     return {"message": "Welcome Admin"}

# @app.get("/supplier")
# async def supplier(user=Depends(role_required(["supplier"]))):
#     return {"message": "Supplier Dashboard"}

# @app.get("/inventory")
# async def inventory(user=Depends(role_required(["inventory_manager"]))):
#     return {"message": "Inventory Dashboard"}