from typing import Optional
from fastapi import HTTPException
import logging

from app.repositories.product_repository import ProductRepository
from app.repositories.category_repository import CategoryRepository
from app.models.product import build_product_document
from app.schemas.product import ProductCreateRequest, ProductUpdateRequest
from app.utils.sku_generator import generate_sku

logger = logging.getLogger(__name__)


class ProductService:
    def __init__(self, product_repo: ProductRepository, category_repo: CategoryRepository):
        self.product_repo = product_repo
        self.category_repo = category_repo

    # Create 

    async def create_product(self, payload: ProductCreateRequest, created_by: str) -> dict:
        # Validate category exists
        category = await self.category_repo.find_by_id(payload.category_id)
        if not category:
            raise HTTPException(status_code=404, detail="Category not found.")
        if not category["is_active"]:
            raise HTTPException(status_code=400, detail="Cannot add product to an inactive category.")

        # Handle SKU: use provided or auto-generate
        if payload.sku:
            sku = payload.sku.upper().strip()
        else:
            sku = generate_sku(
                brand=payload.brand or "",
                category_name=category["name"],
            )

        # Ensure SKU is unique — regenerate once if collision
        if await self.product_repo.sku_exists(sku):
            if payload.sku:
                raise HTTPException(
                    status_code=409,
                    detail=f"SKU '{sku}' already exists. Use a different SKU or leave it empty to auto-generate."
                )
            # Auto-generate collision — try once more
            sku = generate_sku(brand=payload.brand or "", category_name=category["name"])
            if await self.product_repo.sku_exists(sku):
                raise HTTPException(status_code=409, detail="SKU generation conflict. Please try again.")

        # Build image metadata list from payload
        image_metadata = [img.model_dump() for img in (payload.image_metadata or [])]

        doc = build_product_document(
            name=payload.name,
            sku=sku,
            category_id=payload.category_id,
            cost_price=payload.cost_price,
            selling_price=payload.selling_price,
            created_by=created_by,
            description=payload.description,
            brand=payload.brand,
            supplier_ids=payload.supplier_ids,
            reorder_level=payload.reorder_level,
            tax_percentage=payload.tax_percentage,
            unit=payload.unit.value,
            status=payload.status.value,
            image_metadata=image_metadata,
        )
        created = await self.product_repo.create(doc)
        logger.info(f"Product created: {created['name']} | SKU: {created['sku']} by {created_by}")
        return created

    # Read 

    async def get_product(self, product_id: str) -> dict:
        product = await self.product_repo.find_by_id(product_id)
        if not product:
            raise HTTPException(status_code=404, detail="Product not found.")
        return product

    async def get_product_by_sku(self, sku: str) -> dict:
        product = await self.product_repo.find_by_sku(sku)
        if not product:
            raise HTTPException(status_code=404, detail=f"Product with SKU '{sku}' not found.")
        return product

    async def search_products(
        self,
        query: Optional[str],
        category_id: Optional[str],
        supplier_id: Optional[str],
        status: Optional[str],
        min_price: Optional[float],
        max_price: Optional[float],
        page: int,
        page_size: int,
    ) -> dict:
        # Validate price range
        if min_price is not None and max_price is not None and min_price > max_price:
            raise HTTPException(status_code=400, detail="min_price cannot be greater than max_price.")

        skip = (page - 1) * page_size
        products, total = await self.product_repo.search(
            query_str=query,
            category_id=category_id,
            supplier_id=supplier_id,
            status=status,
            min_price=min_price,
            max_price=max_price,
            skip=skip,
            limit=page_size,
        )
        return {"total": total, "page": page, "page_size": page_size, "products": products}

    # Update 

    async def update_product(
        self,
        product_id: str,
        payload: ProductUpdateRequest,
        updated_by: str,
    ) -> dict:
        product = await self.product_repo.find_by_id(product_id)
        if not product:
            raise HTTPException(status_code=404, detail="Product not found.")

        update_data: dict = {"updated_by": updated_by}

        if payload.name is not None:
            update_data["name"] = payload.name.strip()
        if payload.description is not None:
            update_data["description"] = payload.description
        if payload.brand is not None:
            update_data["brand"] = payload.brand
        if payload.supplier_ids is not None:
            update_data["supplier_ids"] = payload.supplier_ids
        if payload.reorder_level is not None:
            update_data["reorder_level"] = payload.reorder_level
        if payload.tax_percentage is not None:
            update_data["tax_percentage"] = round(payload.tax_percentage, 2)
        if payload.unit is not None:
            update_data["unit"] = payload.unit.value
        if payload.status is not None:
            update_data["status"] = payload.status.value
        if payload.cost_price is not None:
            update_data["cost_price"] = round(payload.cost_price, 2)
        if payload.selling_price is not None:
            update_data["selling_price"] = round(payload.selling_price, 2)
        if payload.image_metadata is not None:
            update_data["image_metadata"] = [img.model_dump() for img in payload.image_metadata]

        # If category is changing, validate the new one
        if payload.category_id is not None:
            category = await self.category_repo.find_by_id(payload.category_id)
            if not category:
                raise HTTPException(status_code=404, detail="Category not found.")
            update_data["category_id"] = payload.category_id

        if len(update_data) == 1:  # only updated_by key
            raise HTTPException(status_code=400, detail="No valid fields provided for update.")

        updated = await self.product_repo.update(product_id, update_data)
        logger.info(f"Product {product_id} updated by {updated_by}")
        return updated

    # Delete 

    async def delete_product(self, product_id: str) -> None:
        product = await self.product_repo.find_by_id(product_id)
        if not product:
            raise HTTPException(status_code=404, detail="Product not found.")
        await self.product_repo.delete(product_id)
        logger.info(f"Product {product_id} deleted.")