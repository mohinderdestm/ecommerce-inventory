from datetime import datetime
from io import BytesIO

from fastapi import HTTPException
from fastapi.responses import StreamingResponse

from app.repositories.report_repository import ReportRepository
from app.repositories.warehouse_repository import WarehouseRepository
from app.utils.report_pdf import generate_report_pdf


class ReportService:
    ACCESS = {
        "stock-summary": {"admin", "manager"},
        "low-stock": {"admin", "manager", "supplier"},
        "top-selling": {"admin", "manager", "supplier"},
        "supplier-purchases": {"admin", "manager", "supplier"},
        "dead-stock": {"admin", "manager", "supplier"},
        "monthly-flow": {"admin", "manager", "supplier"},
    }

    TITLES = {
        "stock-summary": "Stock Summary by Warehouse",
        "low-stock": "Low-Stock Report",
        "top-selling": "Top-Selling Products",
        "supplier-purchases": "Supplier-wise Purchase Report",
        "dead-stock": "Dead Stock Report",
        "monthly-flow": "Monthly Inward vs Outward Report",
    }

    @staticmethod
    def _ensure_access(report_key: str, user: dict):
        allowed_roles = ReportService.ACCESS.get(report_key)
        if not allowed_roles:
            raise HTTPException(status_code=404, detail="Report not found")
        if user.get("role") not in allowed_roles:
            raise HTTPException(status_code=403, detail="Access denied for this report")

    @staticmethod
    def _supplier_scope(user: dict):
        return user.get("email") if user.get("role") == "supplier" else None

    @staticmethod
    def _serialize_datetime(value):
        if hasattr(value, "isoformat"):
            return value.isoformat()
        return value

    @staticmethod
    def _format_currency(value):
        return f"INR {float(value or 0):,.2f}"

    @staticmethod
    def _warehouse_line(warehouses: list[dict]):
        if not warehouses:
            return "No warehouse stock"
        return ", ".join(
            f"{row.get('warehouse_name', 'Warehouse')} ({int(row.get('quantity') or 0)})"
            for row in warehouses
        )

    @staticmethod
    async def _stock_summary_payload():
        rows = await ReportRepository.get_stock_summary()
        warehouse_map = {row["warehouse_id"]: row for row in rows}
        warehouses = await WarehouseRepository.get_all()

        merged_rows = []
        total_units = 0
        for warehouse in warehouses:
            warehouse_id = str(warehouse["_id"])
            aggregate = warehouse_map.get(warehouse_id, {})
            row = {
                "warehouse_id": warehouse_id,
                "warehouse_name": warehouse.get("name"),
                "warehouse_code": warehouse.get("code"),
                "capacity": int(warehouse.get("capacity") or 0),
                "total_units": int(aggregate.get("total_units") or 0),
                "unique_products": int(aggregate.get("unique_products") or 0),
                "unique_variants": int(aggregate.get("unique_variants") or 0),
                "last_updated": ReportService._serialize_datetime(
                    aggregate.get("last_updated")
                ),
            }
            capacity = row["capacity"]
            total_units += row["total_units"]
            row["utilization_pct"] = (
                round((row["total_units"] / capacity) * 100, 2)
                if capacity > 0
                else None
            )
            merged_rows.append(row)

        merged_rows.sort(
            key=lambda row: (-row["total_units"], row["warehouse_name"] or "")
        )
        return {
            "rows": merged_rows,
            "summary": {
                "total_warehouses": len(merged_rows),
                "total_units": total_units,
                "active_warehouses": sum(
                    1 for row in merged_rows if row["total_units"] > 0
                ),
            },
        }

    @staticmethod
    async def _low_stock_payload(user: dict):
        rows = await ReportRepository.get_low_stock_report(
            supplier_email=ReportService._supplier_scope(user)
        )
        normalized_rows = []
        for row in rows:
            normalized_rows.append(
                {
                    **row,
                    "available_stock": int(row.get("available_stock") or 0),
                    "low_stock_threshold": int(row.get("low_stock_threshold") or 0),
                    "warehouses": row.get("warehouses", []),
                }
            )
        return {
            "rows": normalized_rows,
            "summary": {
                "alert_items": len(normalized_rows),
                "zero_stock_items": sum(
                    1 for row in normalized_rows if row["available_stock"] == 0
                ),
                "supplier_scope": "self" if user.get("role") == "supplier" else "all",
            },
        }

    @staticmethod
    async def _top_selling_payload(user: dict, months: int, limit: int):
        rows = await ReportRepository.get_top_selling_report(
            supplier_email=ReportService._supplier_scope(user),
            months=months,
            limit=limit,
        )
        normalized_rows = []
        total_units = 0
        total_revenue = 0.0
        for index, row in enumerate(rows, start=1):
            units_sold = int(row.get("units_sold") or 0)
            gross_revenue = float(row.get("gross_revenue") or 0)
            total_units += units_sold
            total_revenue += gross_revenue
            normalized_rows.append(
                {
                    **row,
                    "rank": index,
                    "units_sold": units_sold,
                    "gross_revenue": gross_revenue,
                    "order_count": int(row.get("order_count") or 0),
                    "last_order_at": ReportService._serialize_datetime(
                        row.get("last_order_at")
                    ),
                }
            )
        return {
            "rows": normalized_rows,
            "summary": {
                "period_months": months,
                "products_ranked": len(normalized_rows),
                "total_units_sold": total_units,
                "gross_revenue": round(total_revenue, 2),
            },
        }

    @staticmethod
    async def _supplier_purchase_payload(user: dict, months: int):
        rows = await ReportRepository.get_supplier_purchase_report(
            supplier_email=ReportService._supplier_scope(user),
            months=months,
        )
        normalized_rows = []
        total_value = 0.0
        for row in rows:
            ordered_value = float(row.get("ordered_value") or 0)
            received_value = float(row.get("received_value") or 0)
            total_value += ordered_value
            normalized_rows.append(
                {
                    **row,
                    "purchase_order_count": int(row.get("purchase_order_count") or 0),
                    "open_purchase_orders": int(row.get("open_purchase_orders") or 0),
                    "ordered_quantity": int(row.get("ordered_quantity") or 0),
                    "received_quantity": int(row.get("received_quantity") or 0),
                    "ordered_value": ordered_value,
                    "received_value": received_value,
                    "last_po_at": ReportService._serialize_datetime(
                        row.get("last_po_at")
                    ),
                }
            )
        return {
            "rows": normalized_rows,
            "summary": {
                "period_months": months,
                "suppliers_covered": len(normalized_rows),
                "ordered_value": round(total_value, 2),
            },
        }

    @staticmethod
    async def _dead_stock_payload(user: dict, inactive_days: int):
        rows = await ReportRepository.get_dead_stock_report(
            supplier_email=ReportService._supplier_scope(user),
            inactive_days=inactive_days,
        )
        normalized_rows = []
        total_units = 0
        now = datetime.utcnow()
        for row in rows:
            available_stock = int(row.get("available_stock") or 0)
            last_outward_raw = row.get("last_outward_at")
            last_outward = (
                last_outward_raw if isinstance(last_outward_raw, datetime) else None
            )
            first_inward_raw = row.get("first_inward_at")
            first_inward = (
                first_inward_raw if isinstance(first_inward_raw, datetime) else None
            )
            anchor_date = last_outward or first_inward
            days_idle = (now - anchor_date).days if anchor_date else None
            total_units += available_stock
            normalized_rows.append(
                {
                    **row,
                    "available_stock": available_stock,
                    "days_idle": days_idle,
                    "first_inward_at": ReportService._serialize_datetime(
                        first_inward_raw
                    ),
                    "last_outward_at": ReportService._serialize_datetime(
                        last_outward_raw
                    ),
                }
            )
        return {
            "rows": normalized_rows,
            "summary": {
                "inactive_days_threshold": inactive_days,
                "dead_stock_items": len(normalized_rows),
                "units_blocked": total_units,
            },
        }

    @staticmethod
    async def _monthly_flow_payload(user: dict, months: int):
        rows = await ReportRepository.get_monthly_inward_outward_report(
            supplier_email=ReportService._supplier_scope(user),
            months=months,
        )
        normalized_rows = []
        total_inward = 0
        total_outward = 0
        for row in rows:
            inward = int(row.get("inward") or 0)
            outward = int(row.get("outward") or 0)
            total_inward += inward
            total_outward += outward
            normalized_rows.append(
                {
                    **row,
                    "inward": inward,
                    "outward": outward,
                    "net": int(row.get("net") or 0),
                    "transaction_count": int(row.get("transaction_count") or 0),
                }
            )
        return {
            "rows": normalized_rows,
            "summary": {
                "period_months": months,
                "total_inward": total_inward,
                "total_outward": total_outward,
                "net_flow": total_inward - total_outward,
            },
        }

    @staticmethod
    async def get_report(
        report_key: str,
        user: dict,
        months: int = 6,
        limit: int = 10,
        inactive_days: int = 60,
    ):
        ReportService._ensure_access(report_key, user)

        if report_key == "stock-summary":
            payload = await ReportService._stock_summary_payload()
        elif report_key == "low-stock":
            payload = await ReportService._low_stock_payload(user)
        elif report_key == "top-selling":
            payload = await ReportService._top_selling_payload(user, months, limit)
        elif report_key == "supplier-purchases":
            payload = await ReportService._supplier_purchase_payload(user, months)
        elif report_key == "dead-stock":
            payload = await ReportService._dead_stock_payload(user, inactive_days)
        elif report_key == "monthly-flow":
            payload = await ReportService._monthly_flow_payload(user, months)
        else:
            raise HTTPException(status_code=404, detail="Report not found")

        return {
            "report_key": report_key,
            "title": ReportService.TITLES[report_key],
            "generated_at": datetime.utcnow().isoformat(),
            "filters": {
                "months": months,
                "limit": limit,
                "inactive_days": inactive_days,
            },
            **payload,
        }

    @staticmethod
    def _pdf_columns(report_key: str):
        return {
            "stock-summary": [
                {"label": "Warehouse", "key": "warehouse_name", "width": 24},
                {"label": "Code", "key": "warehouse_code", "width": 10},
                {"label": "Units", "key": "total_units", "width": 10},
                {"label": "Products", "key": "unique_products", "width": 10},
                {"label": "Variants", "key": "unique_variants", "width": 10},
                {"label": "Util%", "key": "utilization_pct", "width": 8},
            ],
            "low-stock": [
                {"label": "Product", "key": "product_name", "width": 24},
                {"label": "Variant", "key": "variant_name", "width": 18},
                {"label": "Stock", "key": "available_stock", "width": 8},
                {"label": "Thresh", "key": "low_stock_threshold", "width": 8},
                {"label": "Supplier", "key": "supplier_name", "width": 18},
            ],
            "top-selling": [
                {"label": "Rank", "key": "rank", "width": 6},
                {"label": "Product", "key": "product_name", "width": 28},
                {"label": "Units", "key": "units_sold", "width": 8},
                {"label": "Orders", "key": "order_count", "width": 8},
                {"label": "Revenue", "key": "gross_revenue_label", "width": 16},
            ],
            "supplier-purchases": [
                {"label": "Supplier", "key": "supplier_name", "width": 24},
                {"label": "POs", "key": "purchase_order_count", "width": 8},
                {"label": "Ordered", "key": "ordered_quantity", "width": 10},
                {"label": "Received", "key": "received_quantity", "width": 10},
                {"label": "Value", "key": "ordered_value_label", "width": 16},
            ],
            "dead-stock": [
                {"label": "Product", "key": "product_name", "width": 24},
                {"label": "Variant", "key": "variant_name", "width": 18},
                {"label": "Stock", "key": "available_stock", "width": 8},
                {"label": "Idle Days", "key": "days_idle", "width": 10},
                {"label": "Supplier", "key": "supplier_name", "width": 18},
            ],
            "monthly-flow": [
                {"label": "Month", "key": "month", "width": 12},
                {"label": "Inward", "key": "inward", "width": 10},
                {"label": "Outward", "key": "outward", "width": 10},
                {"label": "Net", "key": "net", "width": 10},
                {"label": "Moves", "key": "transaction_count", "width": 10},
            ],
        }[report_key]

    @staticmethod
    def _pdf_rows(report_key: str, rows: list[dict]):
        prepared = []
        for row in rows:
            mapped = dict(row)
            if "gross_revenue" in mapped:
                mapped["gross_revenue_label"] = ReportService._format_currency(
                    mapped["gross_revenue"]
                )
            if "ordered_value" in mapped:
                mapped["ordered_value_label"] = ReportService._format_currency(
                    mapped["ordered_value"]
                )
            prepared.append(mapped)
        return prepared

    @staticmethod
    def _pdf_summary(payload: dict):
        summary = []
        for key, value in (payload.get("summary") or {}).items():
            label = key.replace("_", " ").title()
            if "value" in key or "revenue" in key:
                value = ReportService._format_currency(value)
            summary.append((label, value))
        return summary

    @staticmethod
    async def download_report_pdf(
        report_key: str,
        user: dict,
        months: int = 6,
        limit: int = 10,
        inactive_days: int = 60,
    ):
        payload = await ReportService.get_report(
            report_key,
            user,
            months=months,
            limit=limit,
            inactive_days=inactive_days,
        )
        pdf_bytes, filename = generate_report_pdf(
            title=payload["title"],
            generated_at=payload["generated_at"],
            summary_items=ReportService._pdf_summary(payload),
            columns=ReportService._pdf_columns(report_key),
            rows=ReportService._pdf_rows(report_key, payload.get("rows", [])),
        )
        return StreamingResponse(
            BytesIO(pdf_bytes),
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )
