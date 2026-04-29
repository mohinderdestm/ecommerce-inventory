from fastapi import APIRouter, Depends
from typing import List, Dict, Any

from app.core.database import get_database
from app.utils.dependencies import get_current_user, require_admin_or_inventory_manager
from app.repositories.report_repository import ReportRepository
from app.services.report_service import ReportService
from motor.motor_asyncio import AsyncIOMotorDatabase

router = APIRouter(prefix="/reports", tags=["Reports & Analytics"])

# Only Admin and Inventory Manager can access reports
allow_reports = require_admin_or_inventory_manager

def get_report_service(db: AsyncIOMotorDatabase = Depends(get_database)) -> ReportService:
    repository = ReportRepository(db)
    return ReportService(repository)

@router.get("/stock-summary", response_model=List[Dict[str, Any]], dependencies=[Depends(get_current_user), Depends(allow_reports)])
async def get_stock_summary(service: ReportService = Depends(get_report_service)):
    """Get stock summary aggregated by warehouse."""
    return await service.get_stock_summary_by_warehouse()

@router.get("/low-stock", response_model=List[Dict[str, Any]], dependencies=[Depends(get_current_user), Depends(allow_reports)])
async def get_low_stock(service: ReportService = Depends(get_report_service)):
    """Get products that are below their defined reorder level."""
    return await service.get_low_stock_report()

@router.get("/top-selling", response_model=List[Dict[str, Any]], dependencies=[Depends(get_current_user), Depends(allow_reports)])
async def get_top_selling(limit: int = 10, service: ReportService = Depends(get_report_service)):
    """Get the top selling products based on total quantity sold."""
    return await service.get_top_selling_products(limit)

@router.get("/supplier-purchases", response_model=List[Dict[str, Any]], dependencies=[Depends(get_current_user), Depends(allow_reports)])
async def get_supplier_purchases(service: ReportService = Depends(get_report_service)):
    """Get supplier-wise purchase report based on grand total."""
    return await service.get_supplier_wise_purchase_report()

@router.get("/dead-stock", response_model=List[Dict[str, Any]], dependencies=[Depends(get_current_user), Depends(allow_reports)])
async def get_dead_stock(months: int = 3, service: ReportService = Depends(get_report_service)):
    """Get products with stock > 0 but no outward movement in the given number of months."""
    return await service.get_dead_stock_report(months)

@router.get("/monthly-movement", response_model=List[Dict[str, Any]], dependencies=[Depends(get_current_user), Depends(allow_reports)])
async def get_monthly_movement(service: ReportService = Depends(get_report_service)):
    """Get monthly inward vs outward report for the last 12 months."""
    return await service.get_monthly_inward_outward_report()
