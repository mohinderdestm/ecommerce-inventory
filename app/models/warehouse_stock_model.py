from datetime import datetime


class WarehouseStock:
    def __init__(
        self,
        warehouse_id,
        warehouse_name,
        product_id,
        product_name,
        product_sku,
        variant_sku,
        variant_name,
        quantity,
    ):
        self.warehouse_id = warehouse_id
        self.warehouse_name = warehouse_name
        self.product_id = product_id
        self.product_name = product_name
        self.product_sku = product_sku
        self.variant_sku = variant_sku
        self.variant_name = variant_name
        self.quantity = quantity
        self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def dict(self):
        return {
            "warehouse_id": self.warehouse_id,
            "warehouse_name": self.warehouse_name,
            "product_id": self.product_id,
            "product_name": self.product_name,
            "product_sku": self.product_sku,
            "variant_sku": self.variant_sku,
            "variant_name": self.variant_name,
            "quantity": self.quantity,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }
