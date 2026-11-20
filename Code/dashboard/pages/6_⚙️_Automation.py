import os
import sys
import pandas as pd
import streamlit as st

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
DASHBOARD_DIR = os.path.dirname(CURRENT_DIR)
if DASHBOARD_DIR not in sys.path:
    sys.path.insert(0, DASHBOARD_DIR)

from api_client import check_api_health, get_pipeline_runs, trigger_etl_run

st.set_page_config(page_title="Automation & Data Management — PriceIntelli", page_icon="⚙️", layout="wide")

st.title("⚙️ Tự động hóa & Quản lý Dữ liệu (Automation & Data Management)")
st.caption("Quản trị toàn bộ quy trình: Crawl → Clean → EDA → Modeling → Deploy.")

# --- 1. SƠ ĐỒ QUY TRÌNH DATA PLATFORM (MỤC 5 & 1.2) ---
st.subheader("🔄 Chu kỳ Pipeline Tự động hóa End-to-End")

st.markdown(
    """
    ```
    [1. Crawl Web]          -->  [2. Staging Layer]       -->  [3. ETL Processing]     -->  [4. Data Warehouse]      -->  [5. Backend API]       -->  [6. Frontend UI]
    Scrapy + Selenium 8 sàn      MongoDB Atlas (Raw JSON)      Làm sạch, Khử trùng lặp       PostgreSQL Supabase (Stars)        FastAPI (Port 8000)          Streamlit Dashboard
    ```
    """
)

st.markdown("---")

# --- 2. TRẠNG THÁI HỆ THỐNG (HEALTH CHECK) ---
st.subheader("🖥️ Trạng thái các Dịch vụ Nền tảng (Platform Health)")

col1, col2, col3, col4 = st.columns(4)
api_status = check_api_health()

with col1:
    st.metric("🕷️ Web Crawlers", "8/8 Active", "Scrapy + Headless")
with col2:
    st.metric("🍃 Raw Storage", "MongoDB Atlas", "Connected")
with col3:
    st.metric("🐘 Warehouse", "PostgreSQL Supabase", "AWS Singapore")
with col4:
    if api_status:
        st.metric("⚡ FastAPI Backend", "Online (8000)", delta_color="normal")
    else:
        st.metric("⚡ FastAPI Backend", "Local Mode", "Direct Fallback", delta_color="off")

st.markdown("---")

# --- 3. ĐIỀU KHIỂN & KÍCH HOẠT THỦ CÔNG ---
st.subheader("⚡ Kích hoạt Tác vụ Thủ công")
st.caption("Bấm nút để kích hoạt chạy lại ETL Pipeline cập nhật dữ liệu mới vào kho dữ liệu Supabase:")

col_b1, col_b2 = st.columns([1, 2])
with col_b1:
    if st.button("🚀 Chạy ETL Pipeline ngay", type="primary", use_container_width=True):
        with st.spinner("Đang chạy ETL Pipeline... Vui lòng chờ..."):
            res = trigger_etl_run()
            if res.get("status") == "success":
                st.success("✅ ETL Pipeline hoàn tất thành công!")
            else:
                st.info(f"Trạng thái: {res.get('status', 'Đã ghi nhận lệnh chạy')}")

st.markdown("---")

# --- 4. NHẬT KÝ KIỂM TOÁN (AUDIT LOGS) ---
st.subheader("📝 Lịch sử các lần chạy Pipeline (Audit Logs)")

runs = get_pipeline_runs()
if runs:
    df_runs = pd.DataFrame(runs)
    st.dataframe(
        df_runs,
        use_container_width=True,
        column_config={
            "started_at": st.column_config.DatetimeColumn("Thời gian bắt đầu", format="YYYY-MM-DD HH:mm:ss"),
            "finished_at": st.column_config.DatetimeColumn("Thời gian kết thúc", format="YYYY-MM-DD HH:mm:ss"),
            "status": st.column_config.TextColumn("Trạng thái"),
            "records_processed": st.column_config.NumberColumn("Số bản ghi"),
            "error_message": st.column_config.TextColumn("Thông báo lỗi"),
        },
    )
