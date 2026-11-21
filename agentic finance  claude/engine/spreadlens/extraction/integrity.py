"""Upload integrity checks: type, size, page count, encryption, decompression bombs, macros."""

from __future__ import annotations

import hashlib
import io
import zipfile
from dataclasses import dataclass

from spreadlens.config import Settings

PDF_MAGIC = b"%PDF-"
ZIP_MAGIC = b"PK\x03\x04"
XLSX_MEDIA = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


@dataclass
class IntegrityResult:
    ok: bool
    file_kind: str | None
    media_type: str | None
    sha256: str
    size: int
    page_count: int | None = None
    detail: str = ""
    warnings: list[str] | None = None


class IntegrityError(Exception):
    pass


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def check_upload(filename: str, data: bytes, settings: Settings) -> IntegrityResult:
    digest = sha256_bytes(data)
    size = len(data)
    if size == 0:
        return IntegrityResult(False, None, None, digest, size, detail="Empty file.")
    if size > settings.max_upload_bytes:
        return IntegrityResult(False, None, None, digest, size,
                               detail=f"File exceeds the {settings.max_upload_bytes // (1024 * 1024)} MB upload limit.")
    name = filename.lower()
    if data.startswith(PDF_MAGIC):
        return _check_pdf(data, digest, size, settings)
    if data.startswith(ZIP_MAGIC):
        if name.endswith(".xlsm") or name.endswith(".xlsb") or name.endswith(".xls"):
            return IntegrityResult(False, None, None, digest, size,
                                   detail="Macro-enabled or legacy workbooks are not accepted. Save as .xlsx.")
        return _check_xlsx(data, digest, size, settings)
    return IntegrityResult(False, None, None, digest, size,
                           detail="Unsupported file type. Upload a PDF or an .xlsx workbook.")


def _check_pdf(data: bytes, digest: str, size: int, settings: Settings) -> IntegrityResult:
    from pypdf import PdfReader
    from pypdf.errors import PdfReadError

    try:
        reader = PdfReader(io.BytesIO(data), strict=False)
        if reader.is_encrypted:
            # Try the empty user password (owner-locked PDFs are readable); otherwise reject.
            try:
                if not reader.decrypt(""):
                    raise IntegrityError
            except Exception:
                return IntegrityResult(False, "pdf", "application/pdf", digest, size,
                                       detail="The PDF is password protected. Upload an unencrypted copy.")
        pages = len(reader.pages)
    except PdfReadError as exc:
        return IntegrityResult(False, "pdf", "application/pdf", digest, size, detail=f"Malformed PDF: {type(exc).__name__}.")
    except Exception as exc:  # noqa: BLE001 - malformed input of any kind is rejected, never crashes the API
        return IntegrityResult(False, "pdf", "application/pdf", digest, size, detail=f"Unreadable PDF: {type(exc).__name__}.")
    if pages == 0:
        return IntegrityResult(False, "pdf", "application/pdf", digest, size, detail="The PDF has no pages.")
    if pages > settings.max_pdf_pages:
        return IntegrityResult(False, "pdf", "application/pdf", digest, size, page_count=pages,
                               detail=f"The PDF has {pages} pages; the limit is {settings.max_pdf_pages}.")
    return IntegrityResult(True, "pdf", "application/pdf", digest, size, page_count=pages, detail="ok")


def _check_xlsx(data: bytes, digest: str, size: int, settings: Settings) -> IntegrityResult:
    try:
        zf = zipfile.ZipFile(io.BytesIO(data))
        infos = zf.infolist()
    except zipfile.BadZipFile:
        return IntegrityResult(False, "xlsx", XLSX_MEDIA, digest, size, detail="Corrupt workbook archive.")
    names = {i.filename for i in infos}
    if "[Content_Types].xml" not in names or not any(n.startswith("xl/") for n in names):
        return IntegrityResult(False, "xlsx", XLSX_MEDIA, digest, size, detail="Not an Excel .xlsx workbook.")
    total = sum(i.file_size for i in infos)
    compressed = max(1, sum(i.compress_size for i in infos))
    if total > settings.max_xlsx_uncompressed_bytes or total / compressed > settings.max_xlsx_compression_ratio:
        return IntegrityResult(False, "xlsx", XLSX_MEDIA, digest, size,
                               detail="Workbook expands beyond the decompression limits (possible zip bomb).")
    warnings = []
    if any(n.lower().endswith("vbaproject.bin") for n in names):
        warnings.append("Workbook contains a VBA project; macros are never executed and are ignored.")
    sheets = [n for n in names if n.startswith("xl/worksheets/sheet")]
    if len(sheets) > settings.max_xlsx_sheets:
        return IntegrityResult(False, "xlsx", XLSX_MEDIA, digest, size,
                               detail=f"Workbook has {len(sheets)} sheets; the limit is {settings.max_xlsx_sheets}.")
    return IntegrityResult(True, "xlsx", XLSX_MEDIA, digest, size, page_count=len(sheets), detail="ok", warnings=warnings)
