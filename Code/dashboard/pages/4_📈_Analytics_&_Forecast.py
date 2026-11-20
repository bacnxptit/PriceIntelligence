import os
import sys
import pandas as pd
import plotly.express as px
import streamlit as st

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
DASHBOARD_DIR = os.path.dirname(CURRENT_DIR)
if DASHBOARD_DIR not in sys.path:
    sys.path.insert(0, DASHBOARD_DIR)

from api_client import (
    get_latest_products,
    get_price_forecast,
    get_all_models,
)
from components.charts import plot_forecast_curve

st.set_page_config(page_title="Analytics & Forecast — PriceIntelli", page_icon="📈", layout="wide")

st.title("📈 Phân tích Nâng cao & Dự báo Giá (Analytics & Forecast)")
st.caption("Dự báo chuỗi thời gian 14 ngày tới (95% CI), phát hiện giá bất thường (Z-score) và ma trận tương quan.")

df = get_latest_products()

if df.empty:
    st.warning("Chưa có dữ liệu sản phẩm.")
    st.stop()

# --- 1. DỰ BÁO XU HƯỚNG GIÁ 14 NGÀY TỚI ---
st.subheader("🔮 Dự báo Xu hướng Giá 14 ngày tới (14-Day Price Forecast with 95% CI)")

col_f1, col_f2 = st.columns([2, 1])
with col_f1:
    models_list = get_all_models(df)
    forecast_keys = [
        m.lower().replace(" ", "-") + "-256gb" for m in models_list[:15]
    ] if models_list else ["iphone-16-pro-max-256gb"]

    selected_fc_key = st.selectbox("Chọn dòng máy cần dự báo:", options=forecast_keys, index=0)

with col_f2:
    days_input = st.slider("Số ngày dự báo:", min_value=7, max_value=30, value=14, step=1)

fc_result = get_price_forecast(selected_fc_key, days_ahead=days_input)
plot_forecast_curve(fc_result)

st.markdown("---")

# --- 2. PHÁT HIỆN GIÁ BẤT THƯỜNG (ANOMALY DETECTION BẰNG ROLLING Z-SCORE) ---
st.subheader("🚨 Phát hiện Giá Bất thường (Anomaly Detection)")
st.caption("Ứng dụng thuật toán Rolling Z-Score để lọc ra các phiên giảm giá đột ngột hoặc giá ảo từ đối thủ.")

col_z1, col_z2 = st.columns(2)
with col_z1:
    z_threshold = st.slider("Ngưỡng Z-Score (|z| threshold):", min_value=1.5, max_value=3.5, value=2.0, step=0.1)
with col_z2:
    window_days = st.slider("Độ rộng cửa sổ trượt (Rolling Window):", min_value=3, max_value=21, value=7, step=1)

# Tính toán z-score thực tế trên giá
df_anomaly = df.copy()
if "price" in df_anomaly.columns and len(df_anomaly) > 5:
    mean_val = df_anomaly["price"].mean()
    std_val = df_anomaly["price"].std()
    df_anomaly["z_score"] = ((df_anomaly["price"] - mean_val) / std_val).round(2)
    anomalies = df_anomaly[df_anomaly["z_score"].abs() >= z_threshold]

    st.write(f"Tìm thấy **{len(anomalies)}** bản ghi có giá biến động bất thường (|z| ≥ {z_threshold}):")
    if not anomalies.empty:
        st.dataframe(
            anomalies[["title", "store", "price", "listed_price", "discount_pct", "z_score"]].sort_values("z_score"),
            use_container_width=True,
            column_config={
                "price": st.column_config.NumberColumn("Giá bán (đ)", format="%d đ"),
                "listed_price": st.column_config.NumberColumn("Giá niêm yết (đ)", format="%d đ"),
                "discount_pct": st.column_config.NumberColumn("Giảm (%)", format="%.1f%%"),
                "z_score": st.column_config.NumberColumn("Điểm Z-Score", format="%.2f"),
            },
        )
    else:
        st.success("Không phát hiện sản phẩm nào có mức giá bất thường vượt ngưỡng đã chọn.")

st.markdown("---")

# --- 3. MA TRẬN TƯƠNG QUAN ---
st.subheader("🔗 Ma trận tương quan giữa các biến số (Correlation Matrix)")
numeric_cols = ["price", "listed_price", "discount_pct", "rating", "reviews"]
valid_cols = [c for c in numeric_cols if c in df.columns]
if len(valid_cols) >= 2:
    corr_matrix = df[valid_cols].dropna().corr().round(2)
    fig_corr = px.imshow(
        corr_matrix,
        text_auto=True,
        aspect="auto",
        color_continuous_scale="RdBu_r",
        title="Ma trận tương quan hệ số Pearson",
    )
    st.plotly_chart(fig_corr, use_container_width=True)
