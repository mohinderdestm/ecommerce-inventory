from fastapi import APIRouter, Depends, Query

from app.services.report_service import ReportService
from app.utils.dependencies import get_current_user


router = APIRouter(prefix="/reports", tags=["Reports"])


@router.get("/{report_key}")
async def get_report(
    report_key: str,
    months: int = Query(default=6, ge=1, le=24),
    limit: int = Query(default=10, ge=1, le=25),
    inactive_days: int = Query(default=60, ge=7, le=365),
    user=Depends(get_current_user),
):
    return await ReportService.get_report(
        report_key,
        user,
        months=months,
        limit=limit,
        inactive_days=inactive_days,
    )


@router.get("/{report_key}/pdf")
async def download_report_pdf(
    report_key: str,
    months: int = Query(default=6, ge=1, le=24),
    limit: int = Query(default=10, ge=1, le=25),
    inactive_days: int = Query(default=60, ge=7, le=365),
    user=Depends(get_current_user),
):
    return await ReportService.download_report_pdf(
        report_key,
        user,
        months=months,
        limit=limit,
        inactive_days=inactive_days,
    )
