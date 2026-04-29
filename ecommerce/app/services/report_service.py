from typing import List, Dict, Any
from app.repositories.report_repository import ReportRepository


class ReportService:
    def __init__(self, repository: ReportRepository):
        self.repository = repository

    async def get_stock_summary_by_warehouse(self) -> List[Dict[str, Any]]:
        return await self.repository.get_stock_summary_by_warehouse()

    async def get_low_stock_report(self) -> List[Dict[str, Any]]:
        return await self.repository.get_low_stock_report()

    async def get_top_selling_products(self, limit: int = 10) -> List[Dict[str, Any]]:
        return await self.repository.get_top_selling_products(limit)

    async def get_supplier_wise_purchase_report(self) -> List[Dict[str, Any]]:
        return await self.repository.get_supplier_wise_purchase_report()

    async def get_dead_stock_report(self, months: int = 3) -> List[Dict[str, Any]]:
        return await self.repository.get_dead_stock_report(months)

    async def get_monthly_inward_outward_report(self) -> List[Dict[str, Any]]:
        return await self.repository.get_monthly_inward_outward_report()
