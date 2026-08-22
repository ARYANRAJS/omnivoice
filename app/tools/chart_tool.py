import json
import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

def generate_chart_config(title: str, chart_type: str, labels: List[str], data_series: List[Dict[str, Any]]) -> str:
    """
    Generate JSON payload string for Chart.js interactive rendering in Web UI.
    chart_type: 'bar' | 'line' | 'pie' | 'doughnut'
    """
    colors = [
        "rgba(16, 185, 129, 0.85)",   # Accent Green
        "rgba(0, 210, 255, 0.85)",   # Electric Blue
        "rgba(139, 92, 246, 0.85)",  # Purple
        "rgba(245, 158, 11, 0.85)",  # Amber
        "rgba(239, 68, 68, 0.85)"    # Red
    ]

    border_colors = [
        "#10b981", "#00d2ff", "#8b5cf6", "#f59e0b", "#ef4444"
    ]

    datasets = []
    for idx, series in enumerate(data_series):
        c = colors[idx % len(colors)]
        bc = border_colors[idx % len(border_colors)]
        datasets.append({
            "label": series.get("name", f"Series {idx+1}"),
            "data": series.get("data", []),
            "backgroundColor": c if chart_type in ["bar", "pie", "doughnut"] else "rgba(0, 210, 255, 0.15)",
            "borderColor": bc,
            "borderWidth": 2,
            "fill": chart_type == "line",
            "tension": 0.3
        })

    chart_payload = {
        "title": title,
        "type": chart_type if chart_type in ["bar", "line", "pie", "doughnut"] else "bar",
        "labels": labels,
        "datasets": datasets
    }

    return f"```chart_json\n{json.dumps(chart_payload, indent=2)}\n```"

def create_sample_financial_chart(query: str) -> str:
    """Create financial sample chart based on query terms."""
    q_lower = query.lower()
    if "ipo" in q_lower or "profit" in q_lower or "debt" in q_lower:
        labels = ["Year 1 (2023)", "Year 2 (2024)", "Year 3 (2025)"]
        series = [
            {"name": "Net Profit ($M)", "data": [45, 78, 125]},
            {"name": "Total Debt ($M)", "data": [30, 22, 12]}
        ]
        return generate_chart_config("IPO Company 3-Year Financial Growth & Debt", "bar", labels, series)
    else:
        labels = ["Q1", "Q2", "Q3", "Q4"]
        series = [
            {"name": "Revenue ($M)", "data": [120, 150, 180, 220]},
            {"name": "Expenses ($M)", "data": [80, 95, 110, 130]}
        ]
        return generate_chart_config("Company Performance Metrics", "line", labels, series)
