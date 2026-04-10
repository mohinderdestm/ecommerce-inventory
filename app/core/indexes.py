from app.core.database import db

async def create_indexes():
    # Product indexes
    await db["products"].create_index("sku", unique=True)
    await db["products"].create_index("name")
    await db["products"].create_index("category_id")
    await db["products"].create_index("supplier_ids")
    await db["products"].create_index("status")
    await db["products"].create_index([("name", "text"), ("description", "text")])

    # Category indexes
    await db["categories"].create_index("slug", unique=True)
    await db["categories"].create_index("parent_id")
    await db["categories"].create_index("status")