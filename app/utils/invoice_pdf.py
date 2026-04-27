from datetime import datetime


def _escape_pdf_text(text: str) -> str:
    return (
        str(text)
        .replace("\\", "\\\\")
        .replace("(", "\\(")
        .replace(")", "\\)")
        .replace("\r", " ")
        .replace("\n", " ")
    )


def _truncate(text: str, length: int) -> str:
    value = str(text or "")
    if len(value) <= length:
        return value
    return value[: max(0, length - 3)] + "..."


def _pdf_bytes(objects: list[bytes]) -> bytes:
    out = bytearray()
    out.extend(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
    offsets = [0]

    for idx, obj in enumerate(objects, start=1):
        offsets.append(len(out))
        out.extend(f"{idx} 0 obj\n".encode("ascii"))
        out.extend(obj)
        out.extend(b"\nendobj\n")

    xref_offset = len(out)
    out.extend(f"xref\n0 {len(objects) + 1}\n".encode("ascii"))
    out.extend(b"0000000000 65535 f \n")
    for off in offsets[1:]:
        out.extend(f"{off:010d} 00000 n \n".encode("ascii"))

    out.extend(
        (
            "trailer\n"
            f"<< /Size {len(objects) + 1} /Root 1 0 R >>\n"
            "startxref\n"
            f"{xref_offset}\n"
            "%%EOF"
        ).encode("ascii")
    )
    return bytes(out)


def generate_order_invoice_pdf(order_data: dict) -> tuple[bytes, str]:
    order_id = str(order_data.get("id") or "UNKNOWN")
    order_reference = str(order_data.get("order_reference") or order_id)
    customer_name = str(order_data.get("customer_name") or "Customer")
    customer_email = str(order_data.get("customer_email") or "N/A")
    shipping_address = str(order_data.get("shipping_address") or "N/A")
    payment_method = str(order_data.get("payment_method") or "N/A").upper()
    created_raw = order_data.get("created_at")
    if isinstance(created_raw, datetime):
        created_at = created_raw.strftime("%Y-%m-%d %H:%M:%S UTC")
    else:
        created_at = str(created_raw or datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"))

    items = list(order_data.get("items") or [])
    total_amount = float(order_data.get("total_amount") or 0)

    commands: list[str] = []

    def add_text(
        text: str,
        x: int,
        y: int,
        *,
        size: int = 11,
        font: str = "F1",
        rgb: str = "0.12 0.16 0.25",
    ) -> None:
        commands.append("BT")
        commands.append(f"/{font} {size} Tf")
        commands.append(f"{rgb} rg")
        commands.append(f"{x} {y} Td")
        commands.append(f"({_escape_pdf_text(text)}) Tj")
        commands.append("ET")

    # Header band.
    commands.append("0.08 0.23 0.48 rg")
    commands.append("40 760 515 56 re f")
    add_text("SMART INVENTORY - TAX INVOICE", 54, 790, size=16, font="F2", rgb="1 1 1")
    add_text(f"Invoice Ref: {order_reference}", 54, 772, size=10, font="F1", rgb="0.84 0.93 1")

    # Customer + order details.
    y = 734
    add_text("Bill To", 50, y, size=12, font="F2")
    y -= 18
    add_text(f"Name: {customer_name}", 50, y)
    y -= 15
    add_text(f"Email: {customer_email}", 50, y)
    y -= 15
    add_text(f"Address: {_truncate(shipping_address, 92)}", 50, y)

    add_text("Order Details", 340, 734, size=12, font="F2")
    add_text(f"Order ID: {order_id}", 340, 716)
    add_text(f"Order Date: {created_at}", 340, 701)
    add_text(f"Payment Method: {payment_method}", 340, 686)
    add_text("Status: ORDER PLACED", 340, 671)

    # Table header.
    commands.append("0.88 0.92 0.98 rg")
    commands.append("40 626 515 24 re f")
    add_text("Item", 50, 633, size=11, font="F2")
    add_text("Qty", 355, 633, size=11, font="F2")
    add_text("Unit Price", 400, 633, size=11, font="F2")
    add_text("Amount", 485, 633, size=11, font="F2")

    y = 610
    max_items = 16
    rendered_items = items[:max_items]
    for item in rendered_items:
        qty = int(item.get("quantity") or 0)
        unit_price = float(item.get("price_at_purchase") or 0)
        amount = qty * unit_price
        item_name = _truncate(item.get("name") or item.get("product_id") or "Item", 50)

        add_text(item_name, 50, y, size=10)
        add_text(str(qty), 357, y, size=10)
        add_text(f"INR {unit_price:.2f}", 395, y, size=10)
        add_text(f"INR {amount:.2f}", 470, y, size=10)
        y -= 18

    if len(items) > max_items:
        add_text(f"... {len(items) - max_items} more item(s) not shown", 50, y, size=10)
        y -= 16

    # Divider + total.
    commands.append("0.75 0.8 0.88 RG")
    commands.append(f"40 {y - 2} m 555 {y - 2} l S")
    y -= 22

    add_text("Grand Total", 390, y, size=12, font="F2")
    add_text(f"INR {total_amount:.2f}", 470, y, size=12, font="F2")

    # Footer.
    add_text(
        "Thank you for your order. This is a computer-generated invoice.",
        50,
        70,
        size=9,
        rgb="0.35 0.4 0.48",
    )

    stream_text = "\n".join(commands) + "\n"
    stream_bytes = stream_text.encode("latin-1", "replace")

    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Contents 4 0 R /Resources << /Font << /F1 5 0 R /F2 6 0 R >> >> >>",
        b"<< /Length "
        + str(len(stream_bytes)).encode("ascii")
        + b" >>\nstream\n"
        + stream_bytes
        + b"endstream",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold >>",
    ]

    filename = f"Invoice_{order_reference}.pdf".replace(" ", "_")
    return _pdf_bytes(objects), filename
