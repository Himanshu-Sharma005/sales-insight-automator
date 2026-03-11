from fastapi import APIRouter, UploadFile, File, Form, HTTPException, BackgroundTasks, status
from fastapi.responses import JSONResponse
import logging

from app.models.schemas import AnalysisResponse, ErrorResponse
from app.services.file_parser import parse_uploaded_file
from app.services.ai_engine import generate_sales_summary
from app.services.email_service import send_summary_email
from app.services.validator import validate_email_address, validate_file

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post(
    "/upload",
    response_model=AnalysisResponse,
    status_code=status.HTTP_200_OK,
    summary="Upload Sales Data & Generate AI Summary",
    description="""
Upload a CSV or Excel file containing sales data. The API will:

1. **Parse** the uploaded file into structured data
2. **Analyze** the data using an LLM (Google Gemini)  
3. **Email** the generated executive summary to the specified recipient

### Supported Formats
- `.csv` — Comma-separated values
- `.xlsx` — Excel 2007+ format

### File Requirements
- Maximum size: **10 MB**
- Must contain tabular data with headers
- Recommended columns: Date, Product, Region, Revenue, Units Sold

### Rate Limiting
- **10 requests per minute** per IP address
    """,
    responses={
        200: {
            "description": "Analysis complete – summary sent to email",
            "content": {
                "application/json": {
                    "example": {
                        "status": "success",
                        "message": "Summary generated and sent to john@company.com",
                        "recipient": "john@company.com",
                        "summary_preview": "Q1 2026 demonstrated strong revenue momentum...",
                        "rows_analyzed": 6,
                        "filename": "sales_q1_2026.csv"
                    }
                }
            }
        },
        400: {"description": "Invalid file type, size, or email address"},
        422: {"description": "File parsing error – check data format"},
        429: {"description": "Rate limit exceeded"},
        500: {"description": "Internal server error"},
    }
)
async def upload_and_analyze(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(
        ...,
        description="Sales data file (.csv or .xlsx, max 10MB)"
    ),
    recipient_email: str = Form(
        ...,
        description="Email address to receive the AI-generated summary",
        example="executive@company.com"
    ),
):
    """
    **Main endpoint** – Upload a sales data file and receive an AI-generated summary via email.

    The analysis covers:
    - Total revenue and units sold
    - Performance by region and product category  
    - Month-over-month trends
    - Status breakdown (Shipped, Delivered, Cancelled)
    - Executive recommendations
    """
    # Validate email
    if not validate_email_address(recipient_email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid email address format."
        )

    # Validate file
    file_content = await file.read()
    validation_error = validate_file(file, file_content)
    if validation_error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=validation_error
        )

    logger.info(f"Processing file: {file.filename} for {recipient_email}")

    # Parse file
    try:
        df, stats = parse_uploaded_file(file_content, file.filename)
    except Exception as e:
        logger.error(f"File parsing failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Could not parse file: {str(e)}"
        )

    # Generate AI summary
    try:
        summary = await generate_sales_summary(df, stats, file.filename)
    except Exception as e:
        logger.error(f"AI generation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"AI analysis failed: {str(e)}"
        )

    # Send email (in background to not block response)
    background_tasks.add_task(
        send_summary_email,
        recipient_email=recipient_email,
        summary=summary,
        filename=file.filename,
        stats=stats
    )

    preview = summary[:300] + "..." if len(summary) > 300 else summary

    return AnalysisResponse(
        status="success",
        message=f"Summary generated and sent to {recipient_email}",
        recipient=recipient_email,
        summary_preview=preview,
        rows_analyzed=stats.get("total_rows", 0),
        filename=file.filename
    )


@router.get(
    "/sample-data",
    summary="Get Sample CSV Data",
    description="Returns a sample CSV string for testing the upload endpoint.",
    tags=["Utilities"]
)
async def get_sample_data():
    """Returns reference test data (sales_q1_2026.csv)."""
    sample = """Date,Product_Category,Region,Units_Sold,Unit_Price,Revenue,Status
2026-01-05,Electronics,North,150,1200,180000,Shipped
2026-01-12,Home Appliances,South,45,450,20250,Shipped
2026-01-20,Electronics,East,80,1100,88000,Delivered
2026-02-15,Electronics,North,210,1250,262500,Delivered
2026-02-28,Home Appliances,North,60,400,24000,Cancelled
2026-03-10,Electronics,West,95,1150,109250,Shipped"""
    return {
        "filename": "sales_q1_2026.csv",
        "description": "Q1 2026 sample sales data with 6 records",
        "data": sample
    }
