from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any
from motor.motor_asyncio import AsyncIOMotorDatabase


class ReportRepository:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db

    async def get_stock_summary_by_warehouse(self) -> List[Dict[str, Any]]:
        pipeline = [
            {
                "$group": {
                    "_id": "$warehouse_id",
                    "total_quantity": {"$sum": "$quantity"},
                    "product_count": {"$sum": 1}
                }
            },
            {
                "$lookup": {
                    "from": "warehouses",
                    "let": {"w_id": {"$toObjectId": "$_id"}},
                    "pipeline": [{"$match": {"$expr": {"$eq": ["$_id", "$$w_id"]}}}],
                    "as": "warehouse_info"
                }
            },
            {
                "$unwind": {
                    "path": "$warehouse_info",
                    "preserveNullAndEmptyArrays": True
                }
            },
            {
                "$project": {
                    "_id": 0,
                    "warehouse_id": "$_id",
                    "warehouse_name": {"$ifNull": ["$warehouse_info.name", "Unknown"]},
                    "total_quantity": 1,
                    "product_count": 1
                }
            },
            {"$sort": {"warehouse_name": 1}}
        ]
        cursor = self.db["warehouse_stock"].aggregate(pipeline)
        return [doc async for doc in cursor]

    async def get_low_stock_report(self) -> List[Dict[str, Any]]:
        pipeline = [
            {
                "$group": {
                    "_id": "$product_id",
                    "total_stock": {"$sum": "$quantity"}
                }
            },
            {
                "$lookup": {
                    "from": "products",
                    "let": {"p_id": {"$toObjectId": "$_id"}},
                    "pipeline": [
                        {"$match": {"$expr": {"$eq": ["$_id", "$$p_id"]}}}
                    ],
                    "as": "product"
                }
            },
            {"$unwind": "$product"},
            {
                "$match": {
                    "$expr": {"$lt": ["$total_stock", "$product.reorder_level"]}
                }
            },
            {
                "$project": {
                    "_id": 0,
                    "product_id": "$_id",
                    "product_name": "$product.name",
                    "sku": "$product.sku",
                    "total_stock": 1,
                    "reorder_level": "$product.reorder_level",
                    "shortfall": {"$subtract": ["$product.reorder_level", "$total_stock"]},
                    "status": "$product.status"
                }
            },
            {"$sort": {"shortfall": -1}}
        ]
        cursor = self.db["warehouse_stock"].aggregate(pipeline)
        return [doc async for doc in cursor]

    async def get_top_selling_products(self, limit: int = 10) -> List[Dict[str, Any]]:
        pipeline = [
            {"$match": {"status": {"$in": ["confirmed", "packed", "shipped", "delivered"]}}},
            {"$unwind": "$items"},
            {
                "$group": {
                    "_id": "$items.product_id",
                    "product_name": {"$first": "$items.product_name"},
                    "sku": {"$first": "$items.sku"},
                    "total_quantity_sold": {"$sum": "$items.quantity"},
                    "total_revenue": {"$sum": "$items.total"}
                }
            },
            {"$sort": {"total_quantity_sold": -1}},
            {"$limit": limit},
            {
                "$project": {
                    "_id": 0,
                    "product_id": "$_id",
                    "product_name": 1,
                    "sku": 1,
                    "total_quantity_sold": 1,
                    "total_revenue": 1
                }
            }
        ]
        cursor = self.db["sales_orders"].aggregate(pipeline)
        return [doc async for doc in cursor]

    async def get_supplier_wise_purchase_report(self) -> List[Dict[str, Any]]:
        pipeline = [
            {
                "$group": {
                    "_id": "$supplier_id",
                    "supplier_name": {"$first": "$supplier_name"},
                    "total_orders": {"$sum": 1},
                    "total_purchased_value": {"$sum": "$grand_total"}
                }
            },
            {"$sort": {"total_purchased_value": -1}},
            {
                "$project": {
                    "_id": 0,
                    "supplier_id": "$_id",
                    "supplier_name": 1,
                    "total_orders": 1,
                    "total_purchased_value": 1
                }
            }
        ]
        cursor = self.db["purchase_orders"].aggregate(pipeline)
        return [doc async for doc in cursor]

    async def get_dead_stock_report(self, months: int = 3) -> List[Dict[str, Any]]:
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=30 * months)
        pipeline = [
            {
                "$group": {
                    "_id": "$product_id",
                    "total_stock": {"$sum": "$quantity"}
                }
            },
            {"$match": {"total_stock": {"$gt": 0}}},
            {
                "$lookup": {
                    "from": "inventory_logs",
                    "let": {"pid": "$_id"},
                    "pipeline": [
                        {
                            "$match": {
                                "$expr": {"$eq": ["$product_id", "$$pid"]},
                                "movement_type": {"$in": ["outward", "shipped"]},
                                "timestamp": {"$gte": cutoff_date}
                            }
                        }
                    ],
                    "as": "recent_outward_movements"
                }
            },
            {"$match": {"recent_outward_movements": {"$size": 0}}},
            {
                "$lookup": {
                    "from": "products",
                    "let": {"p_id": {"$toObjectId": "$_id"}},
                    "pipeline": [
                        {"$match": {"$expr": {"$eq": ["$_id", "$$p_id"]}}}
                    ],
                    "as": "product"
                }
            },
            {"$unwind": "$product"},
            {
                "$project": {
                    "_id": 0,
                    "product_id": "$_id",
                    "product_name": "$product.name",
                    "sku": "$product.sku",
                    "total_stock": 1,
                    "cost_price": "$product.cost_price",
                    "dead_stock_value": {"$multiply": ["$total_stock", "$product.cost_price"]}
                }
            },
            {"$sort": {"dead_stock_value": -1}}
        ]
        cursor = self.db["warehouse_stock"].aggregate(pipeline)
        return [doc async for doc in cursor]

    async def get_monthly_inward_outward_report(self) -> List[Dict[str, Any]]:
        pipeline = [
            {
                "$group": {
                    "_id": {
                        "year": {"$year": "$timestamp"},
                        "month": {"$month": "$timestamp"}
                    },
                    "total_inward": {
                        "$sum": {
                            "$cond": [{"$in": ["$movement_type", ["inward", "return", "transfer_in"]]}, "$quantity", 0]
                        }
                    },
                    "total_outward": {
                        "$sum": {
                            "$cond": [{"$in": ["$movement_type", ["outward", "damaged", "expired", "transfer_out"]]}, "$quantity", 0]
                        }
                    }
                }
            },
            {"$sort": {"_id.year": -1, "_id.month": -1}},
            {"$limit": 12},  # Last 12 months
            {
                "$project": {
                    "_id": 0,
                    "year": "$_id.year",
                    "month": "$_id.month",
                    "total_inward": 1,
                    "total_outward": 1,
                    "net_movement": {"$subtract": ["$total_inward", "$total_outward"]}
                }
            }
        ]
        cursor = self.db["inventory_logs"].aggregate(pipeline)
        return [doc async for doc in cursor]
