from fastapi import FastAPI
from app.routes.auth import router as auth_router
from app.routes.products import router as product_router 
from app.routes.suppliers import router as supplier_router
from fastapi.middleware.cors import CORSMiddleware
import app.core.cloudinary_config
from app.routes.warehouses import router as warehouse_router
from app.routes.inventory import router as inventory_router
from app.routes.sales_order import router as sales_order_router
from app.routes.purchase_order import router as purchase_order_router
from app.routes.notification import router as notification_router
from app.routes.report import router as report_router


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
app.include_router(supplier_router)
app.include_router(warehouse_router)
app.include_router(inventory_router)
app.include_router(sales_order_router)
app.include_router(purchase_order_router)
app.include_router(notification_router)
app.include_router(report_router)



@app.get("/")
async def root():
    return {"message": "Server Running"}