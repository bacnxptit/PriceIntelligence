import os
import sys
import pandas as pd
import streamlit as st

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
DASHBOARD_DIR = os.path.dirname(CURRENT_DIR)
if DASHBOARD_DIR not in sys.path:
    sys.path.insert(0, DASHBOARD_DIR)

from api_client import get_latest_products, get_all_models

st.set_page_config(page_title="Products Catalog — PriceIntelli", page_icon="📱", layout="wide")

st.title("📱 Quản lý Danh mục Sản phẩm (Product Catalog)")
st.caption("Tra cứu chi tiết từng SKU, lọc Cửa hàng của mình vs Đối thủ và tình trạng kho hàng.")

df = get_latest_products()

if df.empty:
    st.warning("Chưa có dữ liệu sản phẩm.")
    st.stop()

# --- BỘ LỌC ĐA CHIỀU (SIDEBAR HOẶC TOP BAR) ---
col1, col2, col3, col4 = st.columns(4)

with col1:
    store_types = ["Tất cả sàn", "Cửa hàng của tôi (My Store: CellphoneS)", "Các đối thủ (Competitors)"]
    sel_store_type = st.selectbox("Phân loại cửa hàng:", options=store_types, index=0)

with col2:
    all_models = ["Tất cả dòng máy"] + get_all_models(df)
    sel_model = st.selectbox("Chọn dòng máy:", options=all_models, index=0)

with col3:
    all_stores = ["Tất cả các sàn"] + sorted(df["store"].dropna().unique().tolist())
    sel_store = st.selectbox("Lọc sàn cụ thể:", options=all_stores, index=0)

with col4:
    stock_status = st.selectbox("Tình trạng kho hàng:", options=["Tất cả", "Còn hàng (In Stock)", "Hết hàng"], index=0)

# Lọc dữ liệu
filtered_df = df.copy()

if "My Store" in sel_store_type:
    filtered_df = filtered_df[filtered_df["store"] == "CellphoneS"]
elif "Competitors" in sel_store_type:
    filtered_df = filtered_df[filtered_df["store"] != "CellphoneS"]

if sel_model != "Tất cả dòng máy":
    filtered_df = filtered_df[filtered_df["title"].str.contains(sel_model, case=False, na=False)]

if sel_store != "Tất cả các sàn":
    filtered_df = filtered_df[filtered_df["store"] == sel_store]

if stock_status == "Còn hàng (In Stock)" and "in_stock" in filtered_df.columns:
    filtered_df = filtered_df[filtered_df["in_stock"] == True]
elif stock_status == "Hết hàng" and "in_stock" in filtered_df.columns:
    filtered_df = filtered_df[filtered_df["in_stock"] == False]

# Thống kê nhanh kết quả lọc
st.markdown(f"**Kết quả tìm kiếm:** Tìm thấy **{len(filtered_df):,}** sản phẩm phù hợp.")

# Bảng dữ liệu sản phẩm
display_cols = ["title", "store", "price", "listed_price", "discount_pct", "rating", "reviews", "crawl_date", "url"]
cols_to_render = [c for c in display_cols if c in filtered_df.columns]

st.dataframe(
    filtered_df[cols_to_render].sort_values("price", ascending=True),
    use_container_width=True,
    height=480,
    column_config={
        "price": st.column_config.NumberColumn("Giá bán (đ)", format="%d đ"),
        "listed_price": st.column_config.NumberColumn("Giá niêm yết (đ)", format="%d đ"),
        "discount_pct": st.column_config.NumberColumn("Giảm (%)", format="%.1f%%"),
        "rating": st.column_config.NumberColumn("Đánh giá ⭐", format="%.1f"),
        "reviews": st.column_config.NumberColumn("Lượt xem"),
        "url": st.column_config.LinkColumn("Xem tại sàn"),
    },
)

# Nút xuất CSV
csv_bytes = filtered_df.to_csv(index=False).encode("utf-8-sig")
st.download_button(
    label="📥 Xuất danh sách sản phẩm này ra CSV",
    data=csv_bytes,
    file_name="priceintelli_filtered_products.csv",
    mime="text/csv",
)
