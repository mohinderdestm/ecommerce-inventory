from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv


load_dotenv()

MONGO_URI = os.getenv("MONGO_URL")
DB_NAME = os.getenv("DB_NAME")


client = AsyncIOMotorClient(MONGO_URI)

db = client[DB_NAME]
users_collection = db["users"]
products_collection = db["products"]
suppliers_collection = db["suppliers"]
warehouses_collection = db["warehouses"]
inventory_collection = db["inventory"]
inventory_movements_collection = db["inventory_logs"]
sales_orders_collection = db["sales_orders"]



# Dependency function
async def get_db():
    return db
