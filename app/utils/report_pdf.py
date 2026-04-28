from datetime import datetime


PAGE_WIDTH = 595
PAGE_HEIGHT = 842
LEFT_MARGIN = 40
TOP_Y = 792
BOTTOM_MARGIN = 54
LINE_HEIGHT = 14


def _escape_pdf_text(text: str) -> str:
    return (
        str(text)
        .replace("\\", "\\\\")
        .replace("(", "\\(")
        .replace(")", "\\)")
        .replace("\r", " ")
        .replace("\n", " ")
    )


def _truncate(value, width: int) -> str:
    text = str(value or "")
    if len(text) <= width:
        return text
    if width <= 3:
        return text[:width]
    return text[: width - 3] + "..."


def _format_table_line(columns: list[dict], row: dict) -> str:
    chunks = []
    for column in columns:
        chunks.append(
            _truncate(row.get(column["key"], ""), column["width"]).ljust(
                column["width"]
            )
        )
    return " | ".join(chunks)


def _pdf_bytes(objects: list[bytes]) -> bytes:
    out = bytearray()
    out.extend(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
    offsets = [0]

    for index, obj in enumerate(objects, start=1):
        offsets.append(len(out))
        out.extend(f"{index} 0 obj\n".encode("ascii"))
        out.extend(obj)
        out.extend(b"\nendobj\n")

    xref_offset = len(out)
    out.extend(f"xref\n0 {len(objects) + 1}\n".encode("ascii"))
    out.extend(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        out.extend(f"{offset:010d} 00000 n \n".encode("ascii"))

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


def _wrap_summary(summary_items: list[tuple[str, object]]) -> list[str]:
    if not summary_items:
        return ["No summary available"]
    return [f"{label}: {value}" for label, value in summary_items]


def generate_report_pdf(
    *,
    title: str,
    generated_at: str,
    summary_items: list[tuple[str, object]],
    columns: list[dict],
    rows: list[dict],
) -> tuple[bytes, str]:
    pages: list[list[str]] = []

    def add_text(
        page: list[str],
        text: str,
        x: int,
        y: int,
        *,
        size: int = 10,
        font: str = "F1",
        rgb: str = "0.12 0.16 0.25",
    ):
        page.append("BT")
        page.append(f"/{font} {size} Tf")
        page.append(f"{rgb} rg")
        page.append(f"{x} {y} Td")
        page.append(f"({_escape_pdf_text(text)}) Tj")
        page.append("ET")

    def new_page(page_number: int):
        commands: list[str] = []
        commands.append("0.07 0.15 0.32 rg")
        commands.append(f"{LEFT_MARGIN} 770 515 42 re f")
        add_text(
            commands,
            "SMART INVENTORY REPORT",
            LEFT_MARGIN + 14,
            793,
            size=15,
            font="F2",
            rgb="1 1 1",
        )
        add_text(
            commands,
            title,
            LEFT_MARGIN + 14,
            778,
            size=10,
            font="F1",
            rgb="0.88 0.94 1",
        )
        add_text(
            commands,
            f"Generated: {generated_at}",
            LEFT_MARGIN,
            34,
            size=9,
            rgb="0.4 0.46 0.56",
        )
        add_text(
            commands,
            f"Page {page_number}",
            PAGE_WIDTH - 86,
            34,
            size=9,
            rgb="0.4 0.46 0.56",
        )
        return commands

    header_line = _format_table_line(
        columns,
        {column["key"]: column["label"] for column in columns},
    )

    current_page = new_page(1)
    pages.append(current_page)
    current_y = TOP_Y - 42

    for summary_line in _wrap_summary(summary_items):
        add_text(
            current_page,
            summary_line,
            LEFT_MARGIN,
            current_y,
            size=10,
            font="F2",
            rgb="0.1 0.28 0.52",
        )
        current_y -= LINE_HEIGHT

    current_y -= 8
    add_text(
        current_page,
        header_line,
        LEFT_MARGIN,
        current_y,
        size=9,
        font="F3",
        rgb="0.12 0.16 0.25",
    )
    current_y -= LINE_HEIGHT

    separator = "-" * len(header_line)
    add_text(
        current_page,
        separator,
        LEFT_MARGIN,
        current_y,
        size=9,
        font="F3",
        rgb="0.55 0.62 0.73",
    )
    current_y -= LINE_HEIGHT

    table_rows = rows or [{"empty": "No rows available"}]
    if rows:
        prepared_lines = [_format_table_line(columns, row) for row in table_rows]
    else:
        prepared_lines = ["No rows available"]

    for line in prepared_lines:
        if current_y <= BOTTOM_MARGIN:
            current_page = new_page(len(pages) + 1)
            pages.append(current_page)
            current_y = TOP_Y - 42
            add_text(
                current_page,
                header_line,
                LEFT_MARGIN,
                current_y,
                size=9,
                font="F3",
                rgb="0.12 0.16 0.25",
            )
            current_y -= LINE_HEIGHT
            add_text(
                current_page,
                separator,
                LEFT_MARGIN,
                current_y,
                size=9,
                font="F3",
                rgb="0.55 0.62 0.73",
            )
            current_y -= LINE_HEIGHT
        add_text(current_page, line, LEFT_MARGIN, current_y, size=9, font="F3")
        current_y -= LINE_HEIGHT

    objects: list[bytes] = []
    page_object_ids: list[int] = []
    page_stream_object_ids: list[int] = []
    pages_object_id = 2
    next_object_id = 3

    for _ in pages:
        page_object_ids.append(next_object_id)
        next_object_id += 1
        page_stream_object_ids.append(next_object_id)
        next_object_id += 1

    catalog = b"<< /Type /Catalog /Pages 2 0 R >>"
    page_kids = " ".join(f"{page_id} 0 R" for page_id in page_object_ids)
    pages_object = (
        f"<< /Type /Pages /Kids [{page_kids}] /Count {len(page_object_ids)} >>".encode(
            "ascii"
        )
    )

    objects.append(catalog)
    objects.append(pages_object)

    for page_index, page_commands in enumerate(pages):
        page_object_id = page_object_ids[page_index]
        stream_object_id = page_stream_object_ids[page_index]
        stream_text = "\n".join(page_commands) + "\n"
        stream_bytes = stream_text.encode("latin-1", "replace")
        page_object = (
            f"<< /Type /Page /Parent {pages_object_id} 0 R /MediaBox [0 0 {PAGE_WIDTH} {PAGE_HEIGHT}] "
            f"/Contents {stream_object_id} 0 R /Resources << /Font << /F1 {next_object_id} 0 R /F2 {next_object_id + 1} 0 R /F3 {next_object_id + 2} 0 R >> >> >>"
        ).encode("ascii")
        stream_object = (
            b"<< /Length "
            + str(len(stream_bytes)).encode("ascii")
            + b" >>\nstream\n"
            + stream_bytes
            + b"endstream"
        )
        if len(objects) + 1 != page_object_id:
            raise ValueError("Unexpected PDF page object ordering")
        objects.append(page_object)
        if len(objects) + 1 != stream_object_id:
            raise ValueError("Unexpected PDF stream object ordering")
        objects.append(stream_object)

    objects.append(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")
    objects.append(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold >>")
    objects.append(b"<< /Type /Font /Subtype /Type1 /BaseFont /Courier >>")

    generated = (
        datetime.fromisoformat(generated_at.replace("Z", "+00:00"))
        if generated_at
        else datetime.utcnow()
    )
    filename = f"{title.replace(' ', '_').replace('/', '_')}_{generated.strftime('%Y%m%d_%H%M%S')}.pdf"
    return _pdf_bytes(objects), filename
