from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
import io

def generate_invoice_pdf(order, order_id):
    buffer = io.BytesIO()

    doc = SimpleDocTemplate(buffer, pagesize=letter)
    elements = []

    styles = getSampleStyleSheet()

    elements.append(Paragraph(f"Order Invoice - {order_id}", styles["Title"]))
    elements.append(Paragraph(f"Customer: {order.get('customer_name')}", styles["Normal"]))
    elements.append(Paragraph(" ", styles["Normal"]))

    data = [["Product", "Qty", "Price", "Total"]]

    for item in order["items"]:
        total = item["price"] * item["quantity"]
        data.append([
            item["product_name"],
            item["quantity"],
            f"₹{item['price']}",
            f"₹{total}"
        ])

    table = Table(data)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), colors.grey),
        ("TEXTCOLOR",(0,0),(-1,0),colors.white),
        ("GRID", (0,0), (-1,-1), 1, colors.black)
    ]))

    elements.append(table)
    elements.append(Paragraph(" ", styles["Normal"]))
    elements.append(Paragraph(f"Total Amount: ₹{order.get('total_amount')}", styles["Heading2"]))

    doc.build(elements)

    pdf = buffer.getvalue()
    buffer.close()
    return pdf


def generate_amazon_style_email(order, order_id):
    items_html = ""

    for item in order["items"]:
        total = item["price"] * item["quantity"]

        items_html += f"""
        <tr>
            <td>{item["product_name"]}</td>
            <td align="center">{item["quantity"]}</td>
            <td align="center">₹{item["price"]}</td>
            <td align="center">₹{total}</td>
        </tr>
        """

    return f"""
    <div style="font-family:Arial; max-width:600px; margin:auto; border:1px solid #ddd; padding:20px;">
        
        <h2 style="color:#111;">🛒 Order Update</h2>

        <p>Hello <b>{order.get("customer_name")}</b>,</p>

        <p>Thank you for your order! Your order has been placed successfully.</p>

        <p><b>Order ID:</b> {order_id}</p>

        <table style="width:100%; border-collapse:collapse;">
            <tr style="background:#f5f5f5;">
                <th align="left">Product</th>
                <th>Qty</th>
                <th>Price</th>
                <th>Total</th>
            </tr>
            {items_html}
        </table>

        <h3>Total: ₹{order.get("total_amount")}</h3>

        <p>Your invoice is attached to this email.</p>

        <hr>

        <p style="font-size:12px;color:gray;">
            This is an automated email. Please do not reply.
        </p>

    </div>
    """