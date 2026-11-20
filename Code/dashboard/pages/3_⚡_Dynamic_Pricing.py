import os
import sys
import pandas as pd
import streamlit as st

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
DASHBOARD_DIR = os.path.dirname(CURRENT_DIR)
if DASHBOARD_DIR not in sys.path:
    sys.path.insert(0, DASHBOARD_DIR)

from api_client import get_latest_products, calculate_dynamic_pricing

st.set_page_config(page_title="Dynamic Pricing — PriceIntelli", page_icon="⚡", layout="wide")

st.title("⚡ Chiến lược Định giá Động (Dynamic Pricing Engine)")
st.caption("Tự động gợi ý mức giá bán tối ưu dựa trên chiến lược định vị và giá bán thực tế của đối thủ.")

df = get_latest_products()

if df.empty:
    st.warning("Chưa có dữ liệu sản phẩm.")
    st.stop()

# --- KHU VỰC CẤU HÌNH CHIẾN LƯỢC ---
st.markdown("### 🎯 Thiết lập Chiến lược Định giá")
col_conf1, col_conf2, col_conf3 = st.columns([1, 1, 1])

with col_conf1:
    all_stores = sorted(df["store"].dropna().unique().tolist())
    my_store = st.selectbox(
        "Cửa hàng của tôi (My Store):",
        options=all_stores,
        index=all_stores.index("CellphoneS") if "CellphoneS" in all_stores else 0,
    )

with col_conf2:
    strategies = [
        "Bằng đối thủ rẻ nhất (Match Lowest)",
        "Rẻ hơn đối thủ rẻ nhất (Undercut by X%)",
        "Bằng giá trung bình thị trường (Match Average)",
        "Định vị cao cấp (Premium / Highest)",
    ]
    selected_strategy = st.selectbox("Chiến lược định giá:", options=strategies, index=1)

with col_conf3:
    undercut_pct = 1.0
    if "Undercut" in selected_strategy:
        undercut_pct = st.slider("Mức rẻ hơn đối thủ (%):", min_value=0.5, max_value=5.0, value=1.0, step=0.5)

# --- CHẠY TÍNH TOÁN ĐỊNH GIÁ ĐỘNG ---
pricing_df = calculate_dynamic_pricing(df, my_store=my_store, strategy=selected_strategy, undercut_pct=undercut_pct)

if pricing_df.empty:
    st.info("Không tìm thấy sản phẩm nào có cả dữ liệu của cửa hàng bạn và đối thủ để so sánh.")
    st.stop()

# --- TỔNG KẾT KHUYẾN NGHỊ ---
num_decrease = (pricing_df["action"] == "Giảm giá 📉").sum()
num_increase = (pricing_df["action"] == "Tăng giá 📈").sum()
num_hold = (pricing_df["action"] == "Giữ nguyên 🟢").sum()

col_m1, col_m2, col_m3, col_m4 = st.columns(4)
col_m1.metric("Tổng SKU phân tích", f"{len(pricing_df)} SKU")
col_m2.metric("Khuyến nghị Giảm giá 📉", f"{num_decrease} SKU", delta=f"-{num_decrease}", delta_color="inverse")
col_m3.metric("Khuyến nghị Tăng giá 📈", f"{num_increase} SKU", delta=f"+{num_increase}", delta_color="normal")
col_m4.metric("Giá đang tối ưu 🟢", f"{num_hold} SKU")

st.markdown("---")

# --- BẢNG KHUYẾN NGHỊ CHI TIẾT ---
st.subheader("📋 Bảng Khuyến nghị Điều chỉnh Giá chi tiết")
st.dataframe(
    pricing_df[[
        "title", "current_price", "cheapest_store", "competitor_min", "competitor_avg",
        "recommended_price", "diff", "diff_pct", "action"
    ]].sort_values("diff_pct", ascending=True),
    use_container_width=True,
    height=450,
    column_config={
        "current_price": st.column_config.NumberColumn("Giá hiện tại", format="%d đ"),
        "competitor_min": st.column_config.NumberColumn("Giá đối thủ Min", format="%d đ"),
        "competitor_avg": st.column_config.NumberColumn("Giá đối thủ TB", format="%d đ"),
        "recommended_price": st.column_config.NumberColumn("Giá đề xuất mới 🎯", format="%d đ"),
        "diff": st.column_config.NumberColumn("Chênh lệch (VND)", format="%+d đ"),
        "diff_pct": st.column_config.NumberColumn("Chênh lệch (%)", format="%+.1f%%"),
        "action": st.column_config.TextColumn("Hành động"),
        "cheapest_store": st.column_config.TextColumn("Đối thủ rẻ nhất"),
    },
)

# Nút xuất bảng giá khuyến nghị
csv_export = pricing_df.to_csv(index=False).encode("utf-8-sig")
st.download_button(
    label="📥 Tải xuống Bảng đề xuất giá mới (CSV)",
    data=csv_export,
    file_name=f"priceintelli_pricing_recommendation_{my_store}.csv",
    mime="text/csv",
)
