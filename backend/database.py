from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
import os

load_dotenv()

MONGO_URL = os.getenv("MONGO_URL")
DB_NAME = os.getenv("DB_NAME")

client = AsyncIOMotorClient (MONGO_URL)
db = client[DB_NAME]

users_collection = db["users"]
products_collection = db["products"]
orders_collection = db["orders"]
warehouse_collection = db["warehouses"]
inventory_collection = db["inventory"]
movement_collection = db["stock_movements"]
warehouse_staff_collection = db["warehouse_staff"]



