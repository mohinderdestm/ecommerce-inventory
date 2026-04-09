from typing import Optional
from fastapi import HTTPException
import logging

from app.repositories.supplier_repository import SupplierRepository
from app.repositories.product_repository import ProductRepository
from app.models.supplier import SupplierStatus, build_supplier_document
from app.schemas.supplier import (
    SupplierCreateRequest,
    SupplierUpdateRequest,
    SupplierProductMapRequest,
)

logger = logging.getLogger(__name__)


class SupplierService:
    def __init__(self, supplier_repo: SupplierRepository, product_repo: ProductRepository):
        self.repo = supplier_repo
        self.product_repo = product_repo

    # Create 

    async def create_supplier(self, payload: SupplierCreateRequest, created_by: str) -> dict:
        # Email uniqueness (only if email is provided)
        if payload.email and await self.repo.email_exists(str(payload.email)):
            raise HTTPException(
                status_code=409,
                detail="A supplier with this email already exists."
            )

        if payload.gst_number and await self.repo.gst_exists(payload.gst_number):
            raise HTTPException(
                status_code=409,
                detail="A supplier with this GST number already exists."
            )

        address_dict = payload.address.model_dump() if payload.address else None

        doc = build_supplier_document(
            name=payload.name,
            created_by=created_by,
            contact_person=payload.contact_person,
            phone=payload.phone,
            email=str(payload.email) if payload.email else None,
            address=address_dict,
            gst_number=payload.gst_number,
            payment_terms=payload.payment_terms.value,
            rating=payload.rating,
            notes=payload.notes,
        )
        created = await self.repo.create(doc)
        logger.info(f"Supplier created: {created['name']} by {created_by}")
        return created

    # Read 

    async def get_supplier(self, supplier_id: str) -> dict:
        supplier = await self.repo.find_by_id(supplier_id)
        if not supplier:
            raise HTTPException(status_code=404, detail="Supplier not found.")
        return supplier

    async def list_suppliers(
        self,
        status: Optional[str],
        search: Optional[str],
        page: int,
        page_size: int,
    ) -> dict:
        skip = (page - 1) * page_size
        suppliers, total = await self.repo.list_suppliers(
            status=status,
            search=search,
            skip=skip,
            limit=page_size,
        )
        return {"total": total, "page": page, "page_size": page_size, "suppliers": suppliers}

    async def get_suppliers_for_product(self, product_id: str) -> list[dict]:
        
        product = await self.product_repo.find_by_id(product_id)
        if not product:
            raise HTTPException(status_code=404, detail="Product not found.")
        return await self.repo.find_by_product_id(product_id)

    # Update 

    async def update_supplier(
        self,
        supplier_id: str,
        payload: SupplierUpdateRequest,
        updated_by: str,
    ) -> dict:
        supplier = await self.repo.find_by_id(supplier_id)
        if not supplier:
            raise HTTPException(status_code=404, detail="Supplier not found.")

        update_data: dict = {"updated_by": updated_by}

        if payload.name is not None:
            update_data["name"] = payload.name.strip()
        if payload.contact_person is not None:
            update_data["contact_person"] = payload.contact_person
        if payload.phone is not None:
            update_data["phone"] = payload.phone
        if payload.notes is not None:
            update_data["notes"] = payload.notes
        if payload.payment_terms is not None:
            update_data["payment_terms"] = payload.payment_terms.value
        if payload.rating is not None:
            update_data["rating"] = round(max(0.0, min(5.0, payload.rating)), 1)
        if payload.address is not None:
            update_data["address"] = payload.address.model_dump()

        if payload.email is not None:
            email_str = str(payload.email)
            if await self.repo.email_exists(email_str, exclude_id=supplier_id):
                raise HTTPException(
                    status_code=409,
                    detail="A supplier with this email already exists."
                )
            update_data["email"] = email_str.lower()

        if payload.gst_number is not None:
            if await self.repo.gst_exists(payload.gst_number, exclude_id=supplier_id):
                raise HTTPException(
                    status_code=409,
                    detail="A supplier with this GST number already exists."
                )
            update_data["gst_number"] = payload.gst_number.upper()

        if payload.status is not None:
            update_data["status"] = payload.status.value
            update_data["is_active"] = (payload.status == SupplierStatus.ACTIVE)

        if len(update_data) == 1:
            raise HTTPException(status_code=400, detail="No valid fields provided for update.")

        updated = await self.repo.update(supplier_id, update_data)
        logger.info(f"Supplier {supplier_id} updated by {updated_by}")
        return updated

    # Delete

    async def delete_supplier(self, supplier_id: str) -> None:
        supplier = await self.repo.find_by_id(supplier_id)
        if not supplier:
            raise HTTPException(status_code=404, detail="Supplier not found.")

        # Prevent deletion if supplier is linked to any products
        if supplier.get("product_ids"):
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Cannot delete supplier — they are linked to "
                    f"{len(supplier['product_ids'])} product(s). "
                    f"Remove product mappings first."
                )
            )

        await self.repo.delete(supplier_id)
        logger.info(f"Supplier {supplier_id} deleted.")

    # Supplier-Product Mapping

    async def link_products(
        self,
        supplier_id: str,
        payload: SupplierProductMapRequest,
        updated_by: str,
    ) -> dict:
        supplier = await self.repo.find_by_id(supplier_id)
        if not supplier:
            raise HTTPException(status_code=404, detail="Supplier not found.")

        # Validate each product exists
        invalid = []
        for pid in payload.product_ids:
            if not await self.product_repo.find_by_id(pid):
                invalid.append(pid)
        if invalid:
            raise HTTPException(
                status_code=404,
                detail=f"These product IDs were not found: {invalid}"
            )

        updated = await self.repo.add_products(supplier_id, payload.product_ids)

        # Also update supplier_ids on each product document
        for pid in payload.product_ids:
            product = await self.product_repo.find_by_id(pid)
            if product and supplier_id not in product.get("supplier_ids", []):
                existing = product.get("supplier_ids", [])
                existing.append(supplier_id)
                await self.product_repo.update(pid, {"supplier_ids": existing})

        logger.info(f"Linked {len(payload.product_ids)} product(s) to supplier {supplier_id}")
        return updated

    async def unlink_products(
        self,
        supplier_id: str,
        payload: SupplierProductMapRequest,
        updated_by: str,
    ) -> dict:
        supplier = await self.repo.find_by_id(supplier_id)
        if not supplier:
            raise HTTPException(status_code=404, detail="Supplier not found.")

        updated = await self.repo.remove_products(supplier_id, payload.product_ids)

        # Also remove supplier_id from each product's supplier_ids
        for pid in payload.product_ids:
            product = await self.product_repo.find_by_id(pid)
            if product:
                existing = [s for s in product.get("supplier_ids", []) if s != supplier_id]
                await self.product_repo.update(pid, {"supplier_ids": existing})

        logger.info(f"Unlinked {len(payload.product_ids)} product(s) from supplier {supplier_id}")
        return updated

    # Rating Update 

    async def update_rating(self, supplier_id: str, rating: float, updated_by: str) -> dict:
        if not 0 <= rating <= 5:
            raise HTTPException(status_code=400, detail="Rating must be between 0 and 5.")
        supplier = await self.repo.find_by_id(supplier_id)
        if not supplier:
            raise HTTPException(status_code=404, detail="Supplier not found.")
        updated = await self.repo.update(
            supplier_id,
            {"rating": round(rating, 1), "updated_by": updated_by}
        )
        logger.info(f"Supplier {supplier_id} rated {rating} by {updated_by}")
        return updated