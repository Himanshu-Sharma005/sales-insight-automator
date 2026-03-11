from pydantic import BaseModel, EmailStr, Field
from typing import Optional


class AnalysisResponse(BaseModel):
    status: str = Field(..., description="Request status: 'success' or 'error'", example="success")
    message: str = Field(..., description="Human-readable result message", example="Summary sent to john@company.com")
    recipient: str = Field(..., description="Email address the summary was sent to", example="john@company.com")
    summary_preview: str = Field(..., description="First 300 characters of the generated summary")
    rows_analyzed: int = Field(..., description="Number of data rows processed", example=6)
    filename: str = Field(..., description="Name of the uploaded file", example="sales_q1_2026.csv")

    model_config = {
        "json_schema_extra": {
            "example": {
                "status": "success",
                "message": "Summary generated and sent to exec@company.com",
                "recipient": "exec@company.com",
                "summary_preview": "Q1 2026 Sales Performance Summary\n\nThe quarter demonstrated exceptional momentum in the Electronics category, contributing 84% of total revenue...",
                "rows_analyzed": 6,
                "filename": "sales_q1_2026.csv"
            }
        }
    }


class ErrorResponse(BaseModel):
    status: str = Field(default="error")
    detail: str = Field(..., description="Error description")
    code: Optional[int] = Field(None, description="HTTP status code")
