import re
from fastapi import UploadFile
from typing import Optional

ALLOWED_EXTENSIONS = {"csv", "xlsx", "xls"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB
EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$")


def validate_email_address(email: str) -> bool:
    """Validate email format using regex."""
    if not email or len(email) > 254:
        return False
    return bool(EMAIL_REGEX.match(email.strip()))


def validate_file(file: UploadFile, content: bytes) -> Optional[str]:
    """
    Validate uploaded file. Returns error message string or None if valid.
    Checks:
    - File extension is allowed
    - File size is within limit
    - File has a name
    """
    if not file.filename:
        return "No filename provided."

    ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    if ext not in ALLOWED_EXTENSIONS:
        return f"File type '.{ext}' is not supported. Please upload .csv or .xlsx files."

    if len(content) == 0:
        return "Uploaded file is empty."

    if len(content) > MAX_FILE_SIZE:
        size_mb = len(content) / (1024 * 1024)
        return f"File too large ({size_mb:.1f}MB). Maximum allowed size is 10MB."

    # Basic magic byte check for Excel
    if ext in ("xlsx", "xls"):
        # XLSX files start with PK (ZIP format): 0x50 0x4B
        if not content[:2] == b"PK":
            return "File does not appear to be a valid Excel file."

    return None
