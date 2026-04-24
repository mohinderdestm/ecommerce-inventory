from pydantic import BaseModel, Field


class AssignStockSchema(BaseModel):
    warehouse_id: str
    product_id: str
    variant_sku: str
    quantity: int = Field(..., ge=0)
    reference_type: str = "manual_stock"
    reference_id: str | None = None
    remarks: str | None = None


class TransferStockSchema(BaseModel):
    from_warehouse: str
    to_warehouse: str
    variant_sku: str
    quantity: int = Field(..., gt=0)
    reference_type: str = "warehouse_transfer"
    reference_id: str | None = None
    remarks: str | None = None


class UpdateStockSchema(BaseModel):
    quantity: int = Field(..., ge=0)
    reference_type: str = "manual_adjustment"
    reference_id: str | None = None
    remarks: str | None = None
