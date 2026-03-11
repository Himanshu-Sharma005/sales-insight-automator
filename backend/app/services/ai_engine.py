import os
import json
import logging
import httpx
import pandas as pd
from typing import Dict, Any

logger = logging.getLogger(__name__)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
OPENAI_URL = "https://api.openai.com/v1/chat/completions"


def build_prompt(df: pd.DataFrame, stats: Dict[str, Any], filename: str) -> str:
    """Construct a detailed prompt for the LLM."""
    preview_rows = min(len(df), 20)
    data_preview = df.head(preview_rows).to_csv(index=False)
    stats_json = json.dumps(stats, indent=2, default=str)

    prompt = f"""You are a senior business analyst preparing an executive briefing for C-suite leadership.

Analyze the following sales data from file "{filename}" and produce a professional, narrative executive summary.

## Raw Data Sample (first {preview_rows} rows):
```
{data_preview}
```

## Computed Statistics:
```json
{stats_json}
```

## Instructions:
Write a polished executive summary (400–600 words) that includes:

1. **Executive Overview** – One paragraph summarizing overall performance
2. **Key Metrics** – Bullet points: total revenue, units sold, date range covered
3. **Regional Performance** – Which regions led/lagged and by how much
4. **Product Category Analysis** – Performance breakdown by category
5. **Trend Analysis** – Month-over-month or period trends if date data is available
6. **Risk Flags** – Any anomalies (e.g., cancellations, missing data, outliers)
7. **Strategic Recommendations** – 2–3 actionable recommendations for leadership

Use professional business language. Format with clear section headers. Include specific numbers and percentages where possible. The tone should be confident, data-driven, and concise.
"""
    return prompt


async def generate_sales_summary(df: pd.DataFrame, stats: Dict[str, Any], filename: str) -> str:
    """Call OpenAI API to generate an AI summary."""
    if not OPENAI_API_KEY:
        logger.warning("No OPENAI_API_KEY set – using mock summary")
        return _mock_summary(stats, filename)

    prompt = build_prompt(df, stats, filename)

    payload = {
        "model": OPENAI_MODEL,
        "messages": [
            {
                "role": "system",
                "content": "You are a senior business analyst who writes concise, data-driven executive summaries."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        "temperature": 0.4,
        "max_tokens": 1024,
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            OPENAI_URL,
            json=payload,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {OPENAI_API_KEY}"
            }
        )

    if response.status_code != 200:
        logger.error(f"OpenAI API error: {response.status_code} – {response.text}")
        raise RuntimeError(f"OpenAI API returned {response.status_code}: {response.text[:200]}")

    data = response.json()
    try:
        summary = data["choices"][0]["message"]["content"]
        logger.info("AI summary generated successfully")
        return summary
    except (KeyError, IndexError) as e:
        logger.error(f"Unexpected OpenAI response structure: {data}")
        raise RuntimeError("Could not parse AI response") from e


def _mock_summary(stats: Dict[str, Any], filename: str) -> str:
    """Fallback mock summary when no API key is configured."""
    total_rev = stats.get("total_revenue", 0)
    total_units = stats.get("total_units_sold", 0)
    rows = stats.get("total_rows", 0)

    return f"""## Executive Sales Summary – {filename}

**Executive Overview**

The analyzed dataset covers {rows} transactions with a combined revenue of ${total_rev:,.2f} and {total_units:,} units sold. Performance indicators suggest a competitive quarter with varied regional contributions.

**Key Metrics**
- Total Revenue: ${total_rev:,.2f}
- Total Units Sold: {total_units:,}
- Records Analyzed: {rows}

**Regional Performance**

Regional data indicates distributed sales activity. The North region demonstrated strong Electronics traction, while other regions contributed steadily across Home Appliances and Electronics categories.

**Product Category Analysis**

Electronics emerged as the primary revenue driver, outpacing Home Appliances by a significant margin. This trend aligns with broader consumer electronics demand.

**Risk Flags**

One Cancelled order was identified in the dataset. Investigation into the cancellation root cause is recommended to prevent recurrence.

**Strategic Recommendations**

1. Invest in North region Electronics inventory to capitalize on high-demand trends.
2. Develop retention strategies to reduce order cancellations.
3. Explore Home Appliances growth opportunities in under-performing regions.

*Note: This is a mock summary. Configure GEMINI_API_KEY for full AI-powered analysis.*
"""
