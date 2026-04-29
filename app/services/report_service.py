from app.core.database import db
from datetime import datetime

class ReportService:

    @staticmethod
    async def stock_summary():
        inventory = db["inventory"]

        pipeline = [
               {    
                  "$match": {
                         "warehouse_name": {"$ne": None}
                    }
               },
               {
                    "$group": {
                         "_id": {
                          "warehouse": "$warehouse_name",
                          "product": "$product_name"
                    },
                    "stock": {"$sum": "$stock"}
                }
           },
            {
                    "$project": {
                         "_id": 0,
                         "warehouse": "$_id.warehouse",
                         "product": "$_id.product",
                         "stock": 1
                 }
            },
            {
                    "$sort": {"warehouse": 1}
             }
           ]

        return await inventory.aggregate(pipeline).to_list(None)

    # @staticmethod
    # async def low_stock():
    #     inventory = db["inventory"]

    #     return await inventory.find({"stock": {"$lte": 2}}).to_list(None)
    
    @staticmethod
    async def low_stock():
        inventory = db["inventory"]

        pipeline = [
            {
                "$match": {
                    "stock": {"$lte": 2},   # 🔥 your LOW_STOCK_LIMIT
                    "warehouse_name": {"$ne": None}
                }
            },
            {
                "$project": {
                    "_id": 0,
                    "warehouse": "$warehouse_name",
                    "product": "$product_name",
                    "stock": 1
                }
            },
            {
                "$sort": {"stock": 1}   # lowest first
            }
        ]

        return await inventory.aggregate(pipeline).to_list(None)

    @staticmethod
    async def top_selling():
        orders = db["sales_orders"]   # ✅ FIXED
       

        pipeline = [
             {"$match": {"status": {"$in": ["confirmed", "delivered"]}}},
             {"$unwind": "$items"},
             {
                   "$group": {
                       "_id": {
                          "product": "$items.product_name",
                          "warehouse": "$items.warehouse_name"
                         },
                        "total_sold": {"$sum": "$items.quantity"}
                }
              },
              {
                    "$project": {
                        "_id": 0,
                        "product": "$_id.product",
                        "warehouse": "$_id.warehouse",
                        "total_sold": 1
                    }
                }
            ]
        return await orders.aggregate(pipeline).to_list(None)

    
    @staticmethod
    async def supplier_purchase():
        purchases = db["purchase_orders"]

        pipeline = [
           # break items array
           {"$unwind": "$items"},

        # calculate item total
            {
                "$addFields": {
                    "item_total": {
                         "$multiply": ["$items.quantity", "$items.cost_price"]
                    }
                }
            },

           # group by supplier
            {
               "$group": {
                   "_id": "$supplier_name",
                   "total_spent": {"$sum": "$item_total"},
                   "total_orders": {"$sum": 1}
                }
            },

            # clean output
            {
                "$project": {
                    "_id": 0,
                   "supplier": "$_id",
                   "total_spent": 1,
                   "total_orders": 1
                }
            },

           {"$sort": {"total_spent": -1}}
        ]

        return await purchases.aggregate(pipeline).to_list(None)

    # @staticmethod
    # async def dead_stock():
    #     inventory = db["inventory"]

    #     return await inventory.find({"stock": {"$gt": 0}, "last_moved": None}).to_list(None)
    
    @staticmethod
    async def dead_stock():
        inventory = db["inventory"]

        pipeline = [
            {
                "$lookup": {
                    "from": "inventory_logs",
                    "let": {
                        "p_id": "$product_id",
                        "w_id": "$warehouse_id"
                    },
                    "pipeline": [
                      {
                        "$match": {
                            "$expr": {
                                "$and": [
                                    {"$eq": ["$product_id", "$$p_id"]},
                                    {"$eq": ["$warehouse_id", "$$w_id"]}
                                ]
                            }
                        }
                    }
                ],
                   "as": "logs"
            }
        },
        {
                "$match": {
                   "stock": {"$gt": 0},
                   "logs": {"$size": 0}   
                }
            },
            {
                "$project": {
                   "_id": 0,
                   "warehouse": "$warehouse_name",
                   "product": "$product_name",
                   "stock": 1
                }
            }
        ]

        return await inventory.aggregate(pipeline).to_list(None)

    # @staticmethod
    # async def monthly_movement():
    #     logs = db["inventory_logs"]

    #     pipeline = [
    #         {
    #             "$match": {
    #                 "movement_type": {
    #                     "$in": ["inward", "outward", "transfer", "transfer_out", "order_out"]
    #                 }
    #             }
    #         },
    #         {
    #             "$group": {
    #                 "_id": {
    #                     "year": {"$year": "$timestamp"},
    #                     "month": {"$month": "$timestamp"},
    #                     "type": "$movement_type"
    #                 },
    #                "total": {"$sum": "$quantity"}
    #             }
    #         },
    #         {
    #             "$project": {
    #                 "_id": 0,
    #                 "year": "$_id.year",
    #                 "month": "$_id.month",
    #                 "type": "$_id.type",
    #                 "total": 1
    #             }
    #         },
    #         {
    #             "$sort": {"year": 1, "month": 1}
    #         }
    #     ]

    #     return await logs.aggregate(pipeline).to_list(None)
    
    @staticmethod
    async def monthly_movement():
        logs = db["inventory_logs"]

        pipeline = [
           {
                "$group": {
                    "_id": {
                        "month": {"$month": "$timestamp"},
                        "product": "$product_name",
                        "warehouse": "$warehouse_name",
                        "type": "$movement_type"
                    },
                    "total": {"$sum": "$quantity"}
                }
            },
            {
                "$group": {
                    "_id": {
                        "month": "$_id.month",
                        "product": "$_id.product",
                        "warehouse": "$_id.warehouse"
                    },
                    "inward": {
                        "$sum": {
                           "$cond": [
                               {"$eq": ["$_id.type", "inward"]},
                               "$total",
                                0
                            ]
                        }
                    },
                    "outward": {
                       "$sum": {
                            "$cond": [
                               {
                                   "$in": [
                                       "$_id.type",
                                       ["outward", "order_out", "transfer_out"]
                                    ]
                                },
                                "$total",
                                0
                            ]
                        }
                    }
                }
            },
            {
               "$project": {
                   "_id": 0,
                   "month": "$_id.month",
                   "warehouse": "$_id.warehouse",
                   "product": "$_id.product",
                   "inward": 1,
                   "outward": 1,
                   "net": {"$subtract": ["$inward", "$outward"]}
                }
            },
            {
               "$sort": {
                  "month": 1,
                  "warehouse": 1
                }
            }
        ]

        return await logs.aggregate(pipeline).to_list(None)