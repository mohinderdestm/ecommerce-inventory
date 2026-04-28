from datetime import datetime, timedelta

from app.core.database import db


class ReportRepository:
    @staticmethod
    async def get_stock_summary():
        pipeline = [
            {
                "$group": {
                    "_id": {
                        "warehouse_id": "$warehouse_id",
                        "warehouse_name": "$warehouse_name",
                    },
                    "total_units": {"$sum": {"$ifNull": ["$quantity", 0]}},
                    "unique_products": {"$addToSet": "$product_id"},
                    "unique_variants": {"$addToSet": "$variant_sku"},
                    "last_updated": {
                        "$max": {"$ifNull": ["$updated_at", "$created_at"]}
                    },
                }
            },
            {
                "$lookup": {
                    "from": "warehouses",
                    "localField": "_id.warehouse_id",
                    "foreignField": "_id",
                    "as": "warehouse",
                }
            },
            {"$unwind": {"path": "$warehouse", "preserveNullAndEmptyArrays": True}},
            {
                "$project": {
                    "_id": 0,
                    "warehouse_id": {"$toString": "$_id.warehouse_id"},
                    "warehouse_name": {
                        "$ifNull": ["$warehouse.name", "$_id.warehouse_name"]
                    },
                    "warehouse_code": "$warehouse.code",
                    "capacity": {"$ifNull": ["$warehouse.capacity", 0]},
                    "total_units": 1,
                    "unique_products": {"$size": "$unique_products"},
                    "unique_variants": {"$size": "$unique_variants"},
                    "last_updated": 1,
                }
            },
            {"$sort": {"total_units": -1, "warehouse_name": 1}},
        ]
        return await db["warehouse_stock"].aggregate(pipeline).to_list(length=None)

    @staticmethod
    async def get_low_stock_report(supplier_email: str | None = None):
        match_stage = {"supplier_email": supplier_email} if supplier_email else {}
        pipeline = [
            {"$match": match_stage},
            {
                "$lookup": {
                    "from": "suppliers",
                    "localField": "supplier_email",
                    "foreignField": "email",
                    "as": "supplier",
                }
            },
            {"$unwind": {"path": "$supplier", "preserveNullAndEmptyArrays": True}},
            {
                "$project": {
                    "name": 1,
                    "supplier_email": 1,
                    "supplier_name": {"$ifNull": ["$supplier.name", "$supplier_email"]},
                    "unit": {"$ifNull": ["$unit", "piece"]},
                    "report_items": {
                        "$concatArrays": [
                            [
                                {
                                    "sku": "$sku",
                                    "variant_name": "Base Product",
                                    "threshold": {
                                        "$ifNull": ["$low_stock_threshold", 5]
                                    },
                                }
                            ],
                            {
                                "$map": {
                                    "input": {"$ifNull": ["$variants", []]},
                                    "as": "variant",
                                    "in": {
                                        "sku": "$$variant.sku",
                                        "variant_name": {
                                            "$ifNull": ["$$variant.name", "Variant"]
                                        },
                                        "threshold": {
                                            "$ifNull": [
                                                "$$variant.low_stock_threshold",
                                                {
                                                    "$ifNull": [
                                                        "$low_stock_threshold",
                                                        5,
                                                    ]
                                                },
                                            ]
                                        },
                                    },
                                }
                            },
                        ]
                    },
                }
            },
            {"$unwind": "$report_items"},
            {
                "$lookup": {
                    "from": "warehouse_stock",
                    "let": {"product_id": "$_id", "sku": "$report_items.sku"},
                    "pipeline": [
                        {
                            "$match": {
                                "$expr": {
                                    "$and": [
                                        {"$eq": ["$product_id", "$$product_id"]},
                                        {"$eq": ["$variant_sku", "$$sku"]},
                                    ]
                                }
                            }
                        },
                        {
                            "$group": {
                                "_id": None,
                                "total_stock": {"$sum": {"$ifNull": ["$quantity", 0]}},
                                "warehouses": {
                                    "$push": {
                                        "warehouse_name": "$warehouse_name",
                                        "quantity": {"$ifNull": ["$quantity", 0]},
                                    }
                                },
                            }
                        },
                    ],
                    "as": "stock_summary",
                }
            },
            {
                "$addFields": {
                    "stock_summary": {
                        "$ifNull": [
                            {"$arrayElemAt": ["$stock_summary", 0]},
                            {"total_stock": 0, "warehouses": []},
                        ]
                    }
                }
            },
            {
                "$match": {
                    "$expr": {
                        "$lte": [
                            "$stock_summary.total_stock",
                            "$report_items.threshold",
                        ]
                    }
                }
            },
            {
                "$project": {
                    "_id": 0,
                    "product_id": {"$toString": "$_id"},
                    "product_name": "$name",
                    "supplier_email": 1,
                    "supplier_name": 1,
                    "variant_sku": "$report_items.sku",
                    "variant_name": "$report_items.variant_name",
                    "low_stock_threshold": "$report_items.threshold",
                    "available_stock": "$stock_summary.total_stock",
                    "unit": 1,
                    "warehouses": "$stock_summary.warehouses",
                }
            },
            {"$sort": {"available_stock": 1, "product_name": 1, "variant_name": 1}},
        ]
        return await db["products"].aggregate(pipeline).to_list(length=None)

    @staticmethod
    async def get_top_selling_report(
        supplier_email: str | None = None,
        months: int = 6,
        limit: int = 10,
    ):
        since = datetime.utcnow() - timedelta(days=max(1, months) * 30)
        pipeline = [
            {
                "$match": {
                    "created_at": {"$gte": since},
                    "status": {"$ne": "cancelled"},
                }
            },
            {"$unwind": "$items"},
        ]
        if supplier_email:
            pipeline.append({"$match": {"items.supplier_email": supplier_email}})

        pipeline.extend(
            [
                {
                    "$group": {
                        "_id": {
                            "product_id": "$items.product_id",
                            "variant_sku": {"$ifNull": ["$items.variant_sku", ""]},
                        },
                        "product_name": {"$first": "$items.name"},
                        "supplier_email": {"$first": "$items.supplier_email"},
                        "units_sold": {"$sum": {"$ifNull": ["$items.quantity", 0]}},
                        "gross_revenue": {
                            "$sum": {
                                "$multiply": [
                                    {"$ifNull": ["$items.quantity", 0]},
                                    {"$ifNull": ["$items.price_at_purchase", 0]},
                                ]
                            }
                        },
                        "order_refs": {"$addToSet": "$order_reference"},
                        "last_order_at": {"$max": "$created_at"},
                    }
                },
                {
                    "$project": {
                        "_id": 0,
                        "product_id": "$_id.product_id",
                        "variant_sku": "$_id.variant_sku",
                        "product_name": 1,
                        "supplier_email": 1,
                        "units_sold": 1,
                        "gross_revenue": 1,
                        "order_count": {"$size": "$order_refs"},
                        "last_order_at": 1,
                    }
                },
                {"$sort": {"units_sold": -1, "gross_revenue": -1}},
                {"$limit": max(1, min(limit, 25))},
            ]
        )
        return await db["orders"].aggregate(pipeline).to_list(length=None)

    @staticmethod
    async def get_supplier_purchase_report(
        supplier_email: str | None = None,
        months: int = 6,
    ):
        since = datetime.utcnow() - timedelta(days=max(1, months) * 30)
        query = {"created_at": {"$gte": since}}
        if supplier_email:
            query["supplier_email"] = supplier_email

        pipeline = [
            {"$match": query},
            {"$unwind": {"path": "$items", "preserveNullAndEmptyArrays": True}},
            {
                "$group": {
                    "_id": {
                        "supplier_email": "$supplier_email",
                        "supplier_name": {"$ifNull": ["$supplier_name", "Unknown"]},
                    },
                    "po_numbers": {"$addToSet": "$po_number"},
                    "open_po_numbers": {
                        "$addToSet": {
                            "$cond": [
                                {
                                    "$in": [
                                        "$status",
                                        [
                                            "draft",
                                            "submitted",
                                            "approved",
                                            "partially_received",
                                        ],
                                    ]
                                },
                                "$po_number",
                                "$$REMOVE",
                            ]
                        }
                    },
                    "ordered_quantity": {
                        "$sum": {"$ifNull": ["$items.ordered_quantity", 0]}
                    },
                    "received_quantity": {
                        "$sum": {"$ifNull": ["$items.received_quantity", 0]}
                    },
                    "ordered_value": {
                        "$sum": {
                            "$multiply": [
                                {"$ifNull": ["$items.ordered_quantity", 0]},
                                {"$ifNull": ["$items.unit_cost", 0]},
                            ]
                        }
                    },
                    "received_value": {
                        "$sum": {
                            "$multiply": [
                                {"$ifNull": ["$items.received_quantity", 0]},
                                {"$ifNull": ["$items.unit_cost", 0]},
                            ]
                        }
                    },
                    "last_po_at": {"$max": "$created_at"},
                }
            },
            {
                "$project": {
                    "_id": 0,
                    "supplier_email": "$_id.supplier_email",
                    "supplier_name": "$_id.supplier_name",
                    "purchase_order_count": {"$size": "$po_numbers"},
                    "open_purchase_orders": {"$size": "$open_po_numbers"},
                    "ordered_quantity": 1,
                    "received_quantity": 1,
                    "ordered_value": 1,
                    "received_value": 1,
                    "last_po_at": 1,
                }
            },
            {"$sort": {"ordered_value": -1, "supplier_name": 1}},
        ]
        return await db["purchase_orders"].aggregate(pipeline).to_list(length=None)

    @staticmethod
    async def get_dead_stock_report(
        supplier_email: str | None = None,
        inactive_days: int = 60,
    ):
        cutoff = datetime.utcnow() - timedelta(days=max(1, inactive_days))
        match_stage = {"supplier_email": supplier_email} if supplier_email else {}
        pipeline = [
            {"$match": match_stage},
            {
                "$lookup": {
                    "from": "suppliers",
                    "localField": "supplier_email",
                    "foreignField": "email",
                    "as": "supplier",
                }
            },
            {"$unwind": {"path": "$supplier", "preserveNullAndEmptyArrays": True}},
            {
                "$project": {
                    "name": 1,
                    "supplier_email": 1,
                    "supplier_name": {"$ifNull": ["$supplier.name", "$supplier_email"]},
                    "unit": {"$ifNull": ["$unit", "piece"]},
                    "report_items": {
                        "$concatArrays": [
                            [
                                {
                                    "sku": "$sku",
                                    "variant_name": "Base Product",
                                }
                            ],
                            {
                                "$map": {
                                    "input": {"$ifNull": ["$variants", []]},
                                    "as": "variant",
                                    "in": {
                                        "sku": "$$variant.sku",
                                        "variant_name": {
                                            "$ifNull": ["$$variant.name", "Variant"]
                                        },
                                    },
                                }
                            },
                        ]
                    },
                }
            },
            {"$unwind": "$report_items"},
            {
                "$lookup": {
                    "from": "warehouse_stock",
                    "let": {"product_id": "$_id", "sku": "$report_items.sku"},
                    "pipeline": [
                        {
                            "$match": {
                                "$expr": {
                                    "$and": [
                                        {"$eq": ["$product_id", "$$product_id"]},
                                        {"$eq": ["$variant_sku", "$$sku"]},
                                    ]
                                }
                            }
                        },
                        {
                            "$group": {
                                "_id": None,
                                "total_stock": {"$sum": {"$ifNull": ["$quantity", 0]}},
                                "warehouses": {
                                    "$push": {
                                        "warehouse_name": "$warehouse_name",
                                        "quantity": {"$ifNull": ["$quantity", 0]},
                                    }
                                },
                            }
                        },
                    ],
                    "as": "stock_summary",
                }
            },
            {
                "$addFields": {
                    "stock_summary": {
                        "$ifNull": [
                            {"$arrayElemAt": ["$stock_summary", 0]},
                            {"total_stock": 0, "warehouses": []},
                        ]
                    }
                }
            },
            {
                "$lookup": {
                    "from": "inventory_movements",
                    "let": {"product_id": "$_id", "sku": "$report_items.sku"},
                    "pipeline": [
                        {
                            "$match": {
                                "$expr": {
                                    "$and": [
                                        {"$eq": ["$product_id", "$$product_id"]},
                                        {"$eq": ["$variant_sku", "$$sku"]},
                                        {"$ne": ["$movement_type", "transfer"]},
                                    ]
                                }
                            }
                        },
                        {
                            "$group": {
                                "_id": None,
                                "first_inward_at": {
                                    "$min": {
                                        "$cond": [
                                            {"$gt": ["$delta", 0]},
                                            "$created_at",
                                            None,
                                        ]
                                    }
                                },
                                "last_outward_at": {
                                    "$max": {
                                        "$cond": [
                                            {"$lt": ["$delta", 0]},
                                            "$created_at",
                                            None,
                                        ]
                                    }
                                },
                            }
                        },
                    ],
                    "as": "movement_summary",
                }
            },
            {
                "$addFields": {
                    "movement_summary": {
                        "$ifNull": [
                            {"$arrayElemAt": ["$movement_summary", 0]},
                            {"first_inward_at": None, "last_outward_at": None},
                        ]
                    }
                }
            },
            {
                "$match": {
                    "$expr": {
                        "$and": [
                            {"$gt": ["$stock_summary.total_stock", 0]},
                            {
                                "$or": [
                                    {
                                        "$eq": [
                                            "$movement_summary.last_outward_at",
                                            None,
                                        ]
                                    },
                                    {
                                        "$lt": [
                                            "$movement_summary.last_outward_at",
                                            cutoff,
                                        ]
                                    },
                                ]
                            },
                            {
                                "$or": [
                                    {
                                        "$eq": [
                                            "$movement_summary.first_inward_at",
                                            None,
                                        ]
                                    },
                                    {
                                        "$lt": [
                                            "$movement_summary.first_inward_at",
                                            cutoff,
                                        ]
                                    },
                                ]
                            },
                        ]
                    }
                }
            },
            {
                "$project": {
                    "_id": 0,
                    "product_id": {"$toString": "$_id"},
                    "product_name": "$name",
                    "supplier_email": 1,
                    "supplier_name": 1,
                    "variant_sku": "$report_items.sku",
                    "variant_name": "$report_items.variant_name",
                    "available_stock": "$stock_summary.total_stock",
                    "unit": 1,
                    "warehouses": "$stock_summary.warehouses",
                    "first_inward_at": "$movement_summary.first_inward_at",
                    "last_outward_at": "$movement_summary.last_outward_at",
                }
            },
            {"$sort": {"available_stock": -1, "product_name": 1, "variant_name": 1}},
        ]
        return await db["products"].aggregate(pipeline).to_list(length=None)

    @staticmethod
    async def get_monthly_inward_outward_report(
        supplier_email: str | None = None,
        months: int = 6,
    ):
        since = datetime.utcnow() - timedelta(days=max(1, months) * 30)
        pipeline = [
            {
                "$match": {
                    "created_at": {"$gte": since},
                    "movement_type": {"$ne": "transfer"},
                }
            }
        ]

        if supplier_email:
            pipeline.extend(
                [
                    {
                        "$lookup": {
                            "from": "products",
                            "localField": "product_id",
                            "foreignField": "_id",
                            "as": "product",
                        }
                    },
                    {"$unwind": "$product"},
                    {"$match": {"product.supplier_email": supplier_email}},
                ]
            )

        pipeline.extend(
            [
                {
                    "$group": {
                        "_id": {
                            "$dateToString": {
                                "format": "%Y-%m",
                                "date": "$created_at",
                            }
                        },
                        "inward": {
                            "$sum": {"$cond": [{"$gt": ["$delta", 0]}, "$delta", 0]}
                        },
                        "outward": {
                            "$sum": {
                                "$cond": [
                                    {"$lt": ["$delta", 0]},
                                    {"$abs": "$delta"},
                                    0,
                                ]
                            }
                        },
                        "transaction_count": {"$sum": 1},
                    }
                },
                {
                    "$project": {
                        "_id": 0,
                        "month": "$_id",
                        "inward": 1,
                        "outward": 1,
                        "net": {"$subtract": ["$inward", "$outward"]},
                        "transaction_count": 1,
                    }
                },
                {"$sort": {"month": 1}},
            ]
        )
        return await db["inventory_movements"].aggregate(pipeline).to_list(length=None)
