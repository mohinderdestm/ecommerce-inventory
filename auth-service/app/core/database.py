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
    
    logger.info("Database indexes ensured.")


def get_database():
    return db

