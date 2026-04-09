import random
import string


def generate_sku(name: str) -> str:
    prefix = ''.join([c for c in name if c.isalnum()][:3]).upper()
    suffix = ''.join(random.choices(string.digits, k=5))
    return f"{prefix}-{suffix}"


async def generate_unique_sku(name: str, collection):
    while True:
        sku = generate_sku(name)

        # Check if SKU already exists in DB
        existing = await collection.find_one({"sku": sku})

        if not existing:
            return sku