"""Quick test of the chart engine to verify all chart types render."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from services.chart_engine import render_chart, AVAILABLE_CHARTS

test_params = {
    "bar_chart": {"categories": ["Cloud", "Enterprise", "Services", "Support"], "values": [22.3, 14.2, 8.1, 3.9], "title": "Revenue by Segment ($M)", "value_prefix": "$", "value_suffix": "M", "color_mode": "multi"},
    "line_chart": {"categories": ["Q1", "Q2", "Q3", "Q4"], "values": [32, 38, 42, 48.5], "title": "Quarterly Revenue Trend", "ylabel": "Revenue ($M)", "fill": True},
    "pie_chart": {"categories": ["Cloud", "Enterprise", "Services", "Support"], "values": [46, 29, 17, 8], "title": "Revenue Mix", "donut": True, "explode_max": True},
    "grouped_bar_chart": {"categories": ["Cloud", "Enterprise", "Services"], "series": {"2024": [14.7, 12.0, 6.3], "2025": [22.3, 14.2, 8.1]}, "title": "YoY Revenue Growth"},
    "waterfall_chart": {"categories": ["Base", "Cloud +", "Enterprise +", "Services +", "Total"], "values": [36.2, 7.6, 2.2, 1.8, 0.7], "title": "Revenue Bridge Q4 2024 > Q4 2025", "value_prefix": "$", "value_suffix": "M"},
    "gauge_chart": {"value": 72, "max_value": 100, "title": "Net Promoter Score", "label": "Customer Satisfaction"},
    "kpi_card": {"number": "$48.5M", "label": "Total Q4 Revenue", "trend": "+34%", "color": "blue", "subtitle": "vs $36.2M in Q4 2024"},
    "radar_chart": {"categories": ["Innovation", "Support", "Pricing", "Features", "Reliability"], "values": [82, 88, 65, 78, 90], "title": "Competitive Position", "max_value": 100},
    "treemap_chart": {"categories": ["North America", "Europe", "Asia Pacific", "Rest of World"], "values": [28.5, 12.1, 5.8, 2.1], "title": "Revenue by Region ($M)"},
    "funnel_chart": {"stages": ["Leads", "Qualified", "Proposals", "Negotiations", "Won"], "values": [5000, 2800, 1400, 800, 450], "title": "Sales Pipeline Q4 2025"},
    "stacked_bar_chart": {"categories": ["Q1", "Q2", "Q3", "Q4"], "series": {"Cloud": [15, 17, 19, 22.3], "Enterprise": [11, 12, 13, 14.2], "Services": [5, 6, 7, 8.1]}, "title": "Revenue Composition by Quarter"},
    "sunburst_chart": {"categories": ["Total", "North America", "Europe", "APAC", "US", "Canada", "UK", "Germany"], "values": [48.5, 28.5, 12.1, 7.9, 22.0, 6.5, 7.2, 4.9], "parents": ["", "Total", "Total", "Total", "North America", "North America", "Europe", "Europe"], "title": "Revenue Breakdown"},
    "heatmap_chart": {"x_labels": ["Q1", "Q2", "Q3", "Q4"], "y_labels": ["Cloud", "Enterprise", "Services"], "values": [[15, 17, 19, 22], [11, 12, 13, 14], [5, 6, 7, 8]], "title": "Revenue Heatmap"},
    "scatter_chart": {"x_values": [10, 20, 30, 40, 50], "y_values": [15, 25, 22, 38, 45], "labels": ["A", "B", "C", "D", "E"], "title": "Growth vs Investment", "xlabel": "Investment ($M)", "ylabel": "Growth (%)"},
    "multi_kpi_row": {"items": [{"number": "$48.5M", "label": "Revenue", "trend": "+34%", "color": "blue"}, {"number": "22.4%", "label": "Margin", "trend": "+4.3pp", "color": "emerald"}, {"number": "72", "label": "NPS", "trend": "+8", "color": "violet"}]},
    "icon_stat_grid": {"items": [{"number": "1,200+", "label": "Customers"}, {"number": "99.9%", "label": "Uptime"}, {"number": "24/7", "label": "Support"}, {"number": "45", "label": "Countries"}]},
}

os.makedirs("chart_previews", exist_ok=True)
for name, params in test_params.items():
    try:
        img_bytes = render_chart(name, params)
        path = f"chart_previews/{name}.png"
        with open(path, "wb") as f:
            f.write(img_bytes)
        print(f"OK  {name} ({len(img_bytes):,} bytes) -> {path}")
    except Exception as e:
        print(f"ERR {name}: {e}")

print(f"\nAll chart previews saved to test/chart_previews/")
