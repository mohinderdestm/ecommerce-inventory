# from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
# from reportlab.lib import colors
# from reportlab.lib.styles import getSampleStyleSheet
# from reportlab.lib.pagesizes import letter, landscape
# import io

# def generate_report_pdf(data):
#     buffer = io.BytesIO()

#     doc = SimpleDocTemplate(
#         buffer,
#         pagesize=landscape(letter),
#         rightMargin=20,
#         leftMargin=20,
#         topMargin=30,
#         bottomMargin=20
#     )

#     elements = []
#     styles = getSampleStyleSheet()

#     elements.append(Paragraph("📊 Inventory Report", styles["Title"]))

#     if not data:
#         elements.append(Paragraph("No Data Available", styles["Normal"]))
#     else:
#         headers = ["warehouse", "product", "stock"]
#         table_data = [headers]

#         for row in data:
#              table_data.append([
#                     str(row.get("warehouse", "")),
#                     str(row.get("product", "")),
#                     str(row.get("stock", ""))
#              ])

#         num_cols = len(headers)

#         table = Table(
#             table_data,
#             colWidths=[600 / num_cols] * num_cols   # 🔥 wider table
#         )

#         table.setStyle(TableStyle([
#             ("BACKGROUND", (0, 0), (-1, 0), colors.darkblue),
#             ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),

#             ("FONTSIZE", (0, 0), (-1, 0), 12),
#             ("FONTSIZE", (0, 1), (-1, -1), 10),

#             ("TOPPADDING", (0, 0), (-1, -1), 10),
#             ("BOTTOMPADDING", (0, 0), (-1, -1), 10),

#             ("GRID", (0, 0), (-1, -1), 1, colors.black)
#         ]))

#         elements.append(table)

#     doc.build(elements)

#     pdf = buffer.getvalue()
#     buffer.close()

#     return pdf

from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
import io

def generate_report_pdf(report_type, data):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)

    elements = []

    # ✅ HEADERS BASED ON REPORT
    if report_type == "top-selling":
        headers = ["Warehouse", "Product", "Total Sold"]
        keys = ["warehouse", "product", "total_sold"]
        
    elif report_type == "supplier":
        headers = ["Supplier", "Total Spent", "Total Orders"]
        keys = ["supplier", "total_spent", "total_orders"]
    
    elif report_type == "dead-stock":
        headers = ["Warehouse", "Product", "Stock"]
        keys = ["warehouse", "product", "stock"]
    
    # elif report_type == "monthly":
    #     headers = ["Year", "Month", "Type", "Total"]
    #     keys = ["year", "month", "type", "total"]
    
    elif report_type == "monthly":
       headers = ["Month", "Warehouse", "Product", "Inward", "Outward", "Net"]
       keys = ["month", "warehouse", "product", "inward", "outward", "net"]

    else:  # stock-summary / low-stock
        headers = ["Warehouse", "Product", "Stock"]
        keys = ["warehouse", "product", "stock"]

    table_data = [headers]

    # ✅ ROWS
    for row in data:
        table_data.append([
            row.get(k, "-") for k in keys
        ])

    table = Table(table_data, colWidths=[180, 180, 100])

    table.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), colors.black),
        ("TEXTCOLOR", (0,0), (-1,0), colors.white),
        ("GRID", (0,0), (-1,-1), 1, colors.grey),
        ("ALIGN", (0,0), (-1,-1), "CENTER"),
        ("FONTSIZE", (0,0), (-1,-1), 10),
        ("BOTTOMPADDING", (0,0), (-1,0), 10),
    ]))

    elements.append(table)
    doc.build(elements)

    pdf = buffer.getvalue()
    buffer.close()
    return pdf