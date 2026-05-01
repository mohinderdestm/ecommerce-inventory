from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

client: AsyncIOMotorClient = None
db = None


async def connect_to_mongo():
    global client, db
    try:
        client = AsyncIOMotorClient(settings.MONGO_URL)
        db = client[settings.DB_NAME]

        await client.admin.command("ping")
        logger.info(f"Connected to MongoDB Atlas | database: {settings.DB_NAME}")

        await create_indexes()
    except Exception as e:
        logger.error(f"Failed to connect to MongoDB Atlas: {e}")
        raise 

async def close_mongo_connection():
    global client
    if client:
        client.close()
        logger.info("MongoDB connection closed")

async def create_indexes():
    # Users
    await db["users"].create_index("email", unique=True)
    await db["users"].create_index("username", unique=True)
    await db["users"].create_index("role")

    # Categories
    await db["categories"].create_index("slug", unique=True)
    await db["categories"].create_index("parent_id")
    await db["categories"].create_index("is_active")

    # Products
    await db["products"].create_index("sku", unique=True)
    await db["products"].create_index("category_id")
    await db["products"].create_index("status")
    await db["products"].create_index("supplier_ids")
    await db["products"].create_index([("name", "text"), ("brand", "text"), ("description", "text")])
    
    # Suppliers
    await db["suppliers"].create_index("email", sparse=True)
    await db["suppliers"].create_index("gst_number", sparse=True)
    await db["suppliers"].create_index("status")
    await db["suppliers"].create_index("product_ids")
    await db["suppliers"].create_index([("name", "text"), ("contact_person", "text")])

    # Variants
    await db["variants"].create_index("variant_id", unique=True)
    await db["variants"].create_index("product_id")
    await db["variants"].create_index("sku", unique=True)
    await db["variants"].create_index("is_active")
    await db["variants"].create_index([("product_id", 1), ("is_active", 1)])

    # Warehouses
    await db["warehouses"].create_index("name", unique=True)
    await db["warehouses"].create_index("status")
    await db["warehouses"].create_index("staff_ids")
 
    # Warehouse stock — compound unique per warehouse+product+variant
    await db["warehouse_stock"].create_index(
        [("warehouse_id", 1), ("product_id", 1), ("variant_id", 1)], unique=True
    )
    await db["warehouse_stock"].create_index("product_id")
    await db["warehouse_stock"].create_index("warehouse_id")
 
    # Stock transfers
    await db["stock_transfers"].create_index("from_warehouse_id")
    await db["stock_transfers"].create_index("to_warehouse_id")
    await db["stock_transfers"].create_index("status")
    await db["stock_transfers"].create_index("product_id")

    # Sales Orders
    await db["sales_orders"].create_index("order_number", unique=True)
    await db["sales_orders"].create_index("customer_id")
    await db["sales_orders"].create_index("status")
    await db["sales_orders"].create_index("warehouse_id")
    await db["sales_orders"].create_index("created_at")
    await db["sales_orders"].create_index([("customer_id", 1), ("status", 1)])

    # Audit Logs
    await db["audit_logs"].create_index("entity_type")
    await db["audit_logs"].create_index("entity_id")
    await db["audit_logs"].create_index("user_id")
    await db["audit_logs"].create_index("timestamp")

    logger.info("Database indexes ensured.")


def get_database():
    return db

