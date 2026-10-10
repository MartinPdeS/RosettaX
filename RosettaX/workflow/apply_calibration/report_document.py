"""Low-level PDF pages, objects, text metrics, and serialization."""

from dataclasses import dataclass, field

from .report_styles import (
    HELVETICA_WIDTHS,
    PAGE_HEIGHT,
    PAGE_WIDTH,
)


@dataclass
class _PdfPage:
    commands: list[str] = field(default_factory=list)


def _build_pdf_document(*, pages: list[_PdfPage]) -> bytes:
    catalog_object_id = 1
    pages_object_id = 2
    font_regular_object_id = 3
    font_bold_object_id = 4

    next_object_id = 5
    page_object_ids: list[int] = []
    content_object_ids: list[int] = []
    content_streams: list[bytes] = []

    for page in pages:
        page_object_ids.append(next_object_id)
        next_object_id += 1
        content_object_ids.append(next_object_id)
        next_object_id += 1
        content_streams.append(_build_page_content_stream(page=page))

    kids_text = " ".join(f"{page_object_id} 0 R" for page_object_id in page_object_ids)

    objects: list[bytes] = [
        _format_pdf_object(
            catalog_object_id,
            f"<< /Type /Catalog /Pages {pages_object_id} 0 R >>".encode("latin-1"),
        ),
        _format_pdf_object(
            pages_object_id,
            f"<< /Type /Pages /Count {len(page_object_ids)} /Kids [{kids_text}] >>".encode(
                "latin-1"
            ),
        ),
        _format_pdf_object(
            font_regular_object_id,
            b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        ),
        _format_pdf_object(
            font_bold_object_id,
            b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold >>",
        ),
    ]

    for page_object_id, content_object_id, content_stream in zip(
        page_object_ids, content_object_ids, content_streams, strict=False
    ):
        page_body = (
            f"<< /Type /Page /Parent {pages_object_id} 0 R "
            f"/MediaBox [0 0 {PAGE_WIDTH:.0f} {PAGE_HEIGHT:.0f}] "
            f"/Resources << /Font << /F1 {font_regular_object_id} 0 R /F2 {font_bold_object_id} 0 R >> >> "
            f"/Contents {content_object_id} 0 R >>"
        ).encode("latin-1")
        content_body = (
            b"<< /Length "
            + str(len(content_stream)).encode("ascii")
            + b" >>\nstream\n"
            + content_stream
            + b"\nendstream"
        )
        objects.append(_format_pdf_object(page_object_id, page_body))
        objects.append(_format_pdf_object(content_object_id, content_body))

    header = b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n"
    payload = bytearray(header)
    offsets = [0]

    for object_bytes in objects:
        offsets.append(len(payload))
        payload.extend(object_bytes)

    xref_offset = len(payload)
    payload.extend(f"xref\n0 {len(offsets)}\n".encode("ascii"))
    payload.extend(b"0000000000 65535 f \n")

    for offset in offsets[1:]:
        payload.extend(f"{offset:010d} 00000 n \n".encode("ascii"))

    payload.extend(
        (
            f"trailer\n<< /Size {len(offsets)} /Root {catalog_object_id} 0 R >>\n"
            f"startxref\n{xref_offset}\n%%EOF\n"
        ).encode("ascii")
    )

    return bytes(payload)


def _build_page_content_stream(*, page: _PdfPage) -> bytes:
    return "\n".join(page.commands).encode("latin-1")


def _format_pdf_object(object_id: int, body: bytes) -> bytes:
    return str(object_id).encode("ascii") + b" 0 obj\n" + body + b"\nendobj\n"


def _rgb(color: tuple[float, float, float]) -> str:
    return " ".join(f"{channel:.3f}" for channel in color)


def _measure_helvetica_text(text: str, *, size: float) -> float:
    """Measure axis text using the PDF's standard Helvetica font advances."""
    return (
        size
        * sum(
            HELVETICA_WIDTHS[ord(character) - 32]
            if 32 <= ord(character) <= 126
            else 556
            for character in _sanitize_text(text)
        )
        / 1000.0
    )


def _sanitize_text(value: str) -> str:
    return str(value).encode("latin-1", "replace").decode("latin-1")


def _escape_pdf_text(value: str) -> str:
    return value.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
