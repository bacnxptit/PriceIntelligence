import os
import sys
import pandas as pd
import streamlit as st

# Dam bao import dung thu muc dashboard
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
DASHBOARD_DIR = os.path.dirname(CURRENT_DIR)
if DASHBOARD_DIR not in sys.path:
    sys.path.insert(0, DASHBOARD_DIR)

from api_client import (
    get_latest_products,
    get_dashboard_kpis,
    get_price_history_index,
    get_position_counts,
    generate_alerts,
)
from components.alerts_box import render_alerts
from components.kpi_cards import render_kpis
from components.charts import (
    plot_price_over_time,
    plot_price_position,
    plot_store_comparison,
)

st.set_page_config(page_title="Dashboard — PriceIntelli", page_icon="🏠", layout="wide")

st.markdown("# 🏠 Price Intelligence Executive Dashboard")
st.caption("Bảng điều khiển Giám sát Biến động Giá và Vị thế Cạnh tranh Bán lẻ Công nghệ.")

df = get_latest_products()

# --- 1. HỆ THỐNG CẢNH BÁO ĐẦU TRANG (Mục 3) ---
alerts = generate_alerts(df)
render_alerts(alerts)

st.markdown("---")

# --- 2. HÀNG CHỈ SỐ KPI TỔNG QUAN (Mục 2.3) ---
kpis = get_dashboard_kpis()
kpis["total_products"] = len(df)
kpis["total_stores"] = df["store"].nunique() if not df.empty else 0
render_kpis(kpis, alert_count=len(alerts), current_index=102.4)

st.markdown("---")

# --- 3. BIỂU ĐỒ CHUỖI THỜI GIAN & VỊ THẾ GIÁ (Mục 2.4 & 2.6) ---
col_left, col_right = st.columns([1, 1])

with col_left:
    st.subheader("📉 Chỉ số giá theo thời gian (Historical Index)")
    st.caption("Chỉ số giá chuẩn hóa (mốc 100 điểm) giữa các chuỗi cửa hàng qua các ngày.")
    df_ts = get_price_history_index(days=30)
    plot_price_over_time(df_ts)

with col_right:
    st.subheader("🥧 Tỷ trọng 6 nhóm Vị thế Giá (Price Position)")
    st.caption("Phân bổ sản phẩm: Rẻ nhất, Cao nhất, Dưới TB, Trên TB, Tương đương, Không xác định.")
    df_pos = get_position_counts()
    plot_price_position(df_pos)

st.markdown("---")

# --- 4. SO SÁNH GIÁ ĐA SÀN NHANH ---
st.subheader("⚖️ So sánh giá bán thực tế theo chuỗi cửa hàng")
col_sel, _ = st.columns([2, 2])
with col_sel:
    sample_model = st.selectbox(
        "Chọn dòng máy để so sánh ngay:",
        options=[
            "iPhone 16 Pro Max",
            "iPhone 16 Pro",
            "iPhone 16",
            "iPhone 15 Pro Max",
            "iPhone 15",
            "iPhone 13",
        ],
        index=0,
    )
plot_store_comparison(df, model_name=sample_model)
