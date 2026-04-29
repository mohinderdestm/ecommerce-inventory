from fastapi import APIRouter
from app.services.report_service import ReportService
from app.utils.report_pdf import generate_report_pdf

router = APIRouter(prefix="/reports", tags=["Reports"])

@router.get("/stock-summary")
async def stock_summary():
    return await ReportService.stock_summary()

@router.get("/low-stock")
async def low_stock():
    return await ReportService.low_stock()

@router.get("/top-selling")
async def top_selling():
    return await ReportService.top_selling()

@router.get("/supplier")
async def supplier_report():
    return await ReportService.supplier_purchase()

@router.get("/dead-stock")
async def dead_stock():
    return await ReportService.dead_stock()

@router.get("/monthly")
async def monthly():
    return await ReportService.monthly_movement()


# 🔥 PDF EXPORT
# @router.get("/export/{report_type}")
# async def export_report(report_type: str):
#     try:
#         print("📊 EXPORT REPORT:", report_type)

#         if report_type == "stock-summary":
#             data = await ReportService.stock_summary()

#         elif report_type == "low-stock":
#             data = await ReportService.low_stock()

#         elif report_type == "top-selling":
#             data = await ReportService.top_selling()

#         else:
#             return {"pdf": None}

#         print("📦 DATA:", data)

#         pdf_bytes = generate_report_pdf(data)

#         import base64
#         encoded = base64.b64encode(pdf_bytes).decode("utf-8")

#         return {"pdf": encoded}

#     except Exception as e:
#         print("❌ EXPORT ERROR:", e)
#         return {"pdf": None}

@router.get("/export/{report_type}")
async def export_report(report_type: str):

    if report_type == "stock-summary":
        data = await ReportService.stock_summary()

    elif report_type == "low-stock":
        data = await ReportService.low_stock()

    elif report_type == "top-selling":
        data = await ReportService.top_selling()
    
    elif report_type == "supplier":   # ✅ ADD THIS
        data = await ReportService.supplier_purchase()
   
    elif report_type == "monthly":
        data = await ReportService.monthly_movement()
    else:
        return {"pdf": None}

    print("📊 EXPORT REPORT:", report_type)
    print("📦 DATA:", data)

    pdf_bytes = generate_report_pdf(report_type, data)  # ✅ FIXED

    import base64
    encoded = base64.b64encode(pdf_bytes).decode("utf-8")

    return {"pdf": encoded}