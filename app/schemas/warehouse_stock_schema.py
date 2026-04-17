from pydantic import BaseModel, Field


class AssignStockSchema(BaseModel):
    warehouse_id: str
    product_id: str
    variant_sku: str
    quantity: int = Field(..., ge=0)


class TransferStockSchema(BaseModel):
    from_warehouse: str
    to_warehouse: str
    variant_sku: str
    quantity: int = Field(..., gt=0)


class UpdateStockSchema(BaseModel):
    quantity: int = Field(..., ge=0)
