import os
import sys
import pandas as pd
import plotly.express as px
import streamlit as st

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
DASHBOARD_DIR = os.path.dirname(CURRENT_DIR)
if DASHBOARD_DIR not in sys.path:
    sys.path.insert(0, DASHBOARD_DIR)

from api_client import get_model_metrics_data, predict_price_ml

st.set_page_config(page_title="Model Insights — PriceIntelli", page_icon="🧠", layout="wide")

st.title("🧠 Hiểu biết về Mô hình Học máy (Model Insights)")
st.caption("Đánh giá độ chính xác của mô hình Machine Learning (XGBoost) và trình giả lập định giá thông minh.")

metrics = get_model_metrics_data()

# --- 1. CÁC CHỈ SỐ ĐÁNH GIÁ MÔ HÌNH (MODEL PERFORMANCE) ---
st.subheader("📊 Hiệu suất Mô hình Dự đoán Giá (Model Performance)")

col1, col2, col3, col4 = st.columns(4)
r2_val = metrics.get("r2_score", 0.8624)
mae_val = metrics.get("mae", 4229494.0)
rmse_val = metrics.get("rmse", 6493075.0)
samples_val = metrics.get("total_samples", 265)

col1.metric("Độ chính xác R² Score", f"{r2_val:.4f}", help="Hệ số xác định: mô hình giải thích được >86% biến thiên giá.")
col2.metric("Sai số tuyệt đối (MAE)", f"{mae_val:,.0f} đ", help="Sai số trung bình giữa giá dự đoán và giá thật.")
col3.metric("Căn sai số bình phương (RMSE)", f"{rmse_val:,.0f} đ")
col4.metric("Kích thước tập mẫu", f"{samples_val} sản phẩm", delta="Real Data", delta_color="off")

st.markdown("---")

# --- 2. BIỂU ĐỒ FEATURE IMPORTANCE ---
st.subheader("🎯 Tầm quan trọng của các Đặc trưng (Feature Importance)")
st.caption("Các thuộc tính ảnh hưởng nhiều nhất đến mức giá bán của iPhone trên thị trường.")

feat_dict = metrics.get("feature_importances", {
    "Dung lượng bộ nhớ (capacity_gb)": 0.8125,
    "Thế hệ iPhone (generation)": 0.1032,
    "Dòng Pro (is_pro)": 0.0593,
    "Dòng Pro Max (is_promax)": 0.0069,
    "Dòng Plus (is_plus)": 0.0097,
    "Điểm đánh giá (rating)": 0.0075,
    "Lượt reviews": 0.0009,
})

feat_df = pd.DataFrame([
    {"Đặc trưng": k, "Tầm ảnh hưởng (%)": round(v * 100, 2)}
    for k, v in feat_dict.items()
]).sort_values("Tầm ảnh hưởng (%)", ascending=True)

fig_feat = px.bar(
    feat_df,
    x="Tầm ảnh hưởng (%)",
    y="Đặc trưng",
    orientation="h",
    color="Tầm ảnh hưởng (%)",
    color_continuous_scale="Blues",
    text_auto=".1f",
    title="Độ quan trọng của các biến trong mô hình XGBoost / GBDT",
)
fig_feat.update_layout(margin=dict(l=20, r=20, t=50, b=20), showlegend=False)
st.plotly_chart(fig_feat, use_container_width=True)

st.markdown("---")

# --- 3. TRÌNH GIẢ LẬP ĐỊNH GIÁ (PRICE SIMULATOR) ---
st.subheader("🎮 Trình Giả lập Định giá Sản phẩm (Interactive Price Simulator)")
st.caption("Nhập cấu hình thông số của một chiếc iPhone để mô hình AI định giá thị trường ngay lập tức:")

col_s1, col_s2, col_s3 = st.columns(3)

with col_s1:
    gen_in = st.selectbox("Thế hệ máy (Generation):", options=[13, 14, 15, 16, 17, 18], index=3)
    rom_in = st.select_slider("Dung lượng bộ nhớ:", options=[64, 128, 256, 512, 1024, 2048], value=256)

with col_s2:
    type_in = st.radio("Phiên bản:", options=["Bản Thường (Base)", "Bản Plus", "Bản Pro", "Bản Pro Max"], index=3)
    p_pro = 1 if "Pro" in type_in else 0
    p_promax = 1 if "Pro Max" in type_in else 0
    p_plus = 1 if "Plus" in type_in else 0

with col_s3:
    rate_in = st.slider("Điểm đánh giá ⭐:", min_value=3.5, max_value=5.0, value=4.9, step=0.1)
    rev_in = st.number_input("Số lượt đánh giá:", min_value=0, max_value=5000, value=120)

if st.button("🚀 Dự đoán Giá Thị trường với AI", type="primary", use_container_width=True):
    sample_feat = {
        "generation": gen_in,
        "capacity_gb": rom_in,
        "is_pro": p_pro,
        "is_promax": p_promax,
        "is_plus": p_plus,
        "rating": rate_in,
        "reviews": rev_in,
    }
    pred_res = predict_price_ml(sample_feat)

    st.success(f"### 🏷️ Giá bán thị trường ước tính của AI: **{pred_res:,.0f} VND**")
    st.info(
        f"💡 Khoảng giá cạnh tranh khuyến nghị cho **iPhone {gen_in} {type_in} {rom_in}GB**: "
        f"Từ **{pred_res*0.95:,.0f} đ** đến **{pred_res*1.05:,.0f} đ** (Biên độ dao động thị trường ±5%)."
    )
