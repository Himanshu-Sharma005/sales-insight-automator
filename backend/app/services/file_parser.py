import pandas as pd
import io
from typing import Tuple, Dict, Any
import logging

logger = logging.getLogger(__name__)


def parse_uploaded_file(file_content: bytes, filename: str) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """Parse CSV or Excel file content into a DataFrame and compute stats."""
    ext = filename.rsplit(".", 1)[-1].lower()

    if ext == "csv":
        df = pd.read_csv(io.BytesIO(file_content))
    elif ext in ("xlsx", "xls"):
        df = pd.read_excel(io.BytesIO(file_content))
    else:
        raise ValueError(f"Unsupported file type: .{ext}")

    if df.empty:
        raise ValueError("File contains no data.")

    # Clean column names
    df.columns = [col.strip() for col in df.columns]

    stats = compute_stats(df)
    logger.info(f"Parsed {len(df)} rows from {filename}")
    return df, stats


def compute_stats(df: pd.DataFrame) -> Dict[str, Any]:
    """Compute summary statistics from the DataFrame."""
    stats: Dict[str, Any] = {
        "total_rows": len(df),
        "columns": list(df.columns),
    }

    # Revenue stats
    if "Revenue" in df.columns:
        df["Revenue"] = pd.to_numeric(df["Revenue"], errors="coerce")
        stats["total_revenue"] = float(df["Revenue"].sum())
        stats["avg_revenue"] = float(df["Revenue"].mean())
        stats["max_revenue"] = float(df["Revenue"].max())
        stats["min_revenue"] = float(df["Revenue"].min())

        if "Region" in df.columns:
            stats["revenue_by_region"] = (
                df.groupby("Region")["Revenue"].sum().to_dict()
            )
        if "Product_Category" in df.columns:
            stats["revenue_by_category"] = (
                df.groupby("Product_Category")["Revenue"].sum().to_dict()
            )

    # Units sold
    if "Units_Sold" in df.columns:
        df["Units_Sold"] = pd.to_numeric(df["Units_Sold"], errors="coerce")
        stats["total_units_sold"] = int(df["Units_Sold"].sum())

    # Status breakdown
    if "Status" in df.columns:
        status_counts = df["Status"].value_counts().to_dict()
        stats["status_breakdown"] = {str(k): int(v) for k, v in status_counts.items()}

    # Date range
    if "Date" in df.columns:
        try:
            df["Date"] = pd.to_datetime(df["Date"])
            stats["date_range"] = {
                "start": str(df["Date"].min().date()),
                "end": str(df["Date"].max().date()),
            }
            # Monthly revenue
            df["Month"] = df["Date"].dt.to_period("M").astype(str)
            if "Revenue" in df.columns:
                stats["monthly_revenue"] = (
                    df.groupby("Month")["Revenue"].sum().to_dict()
                )
        except Exception:
            pass

    return stats
