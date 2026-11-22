import os
import streamlit as st
import pandas as pd

from views.css import CUSTOM_CSS
from views.view_dashboard import render_dashboard_view
from views.view_products import render_products_view
from views.view_pricing import render_pricing_view
from views.view_management import render_management_view
from views.view_reports import render_reports_view
from views.view_insights import render_insights_view
from views.view_automation import render_automation_view
from data_loader import load_project_dataset_with_source
from components.ai_assistant import ask_assistant

st.set_page_config(
    page_title="PriceIntelli — Hệ thống Giám sát Giá",
    page_icon="🍎",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Apply exact design system CSS from demo
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# Tự động đồng bộ dữ liệu mới nhất từ PostgreSQL Supabase mỗi 30 phút (TTL=1800s)
@st.cache_data(ttl=1800, show_spinner="Đang đồng bộ dữ liệu mới nhất từ PostgreSQL...")
def get_data():
    return load_project_dataset_with_source()

try:
    df_products, data_source = get_data()
except Exception as e:
    st.error(f"Lỗi đọc dữ liệu dự án: {e}")
    df_products, data_source = pd.DataFrame(), "Offline"

# --- SIDEBAR (THANH BAR BÊN TRÁI VỚI ICON QUẢ TÁO APPLE) ---
with st.sidebar:
    st.markdown("""
    <div class="pi-logo">
        <svg width="26" height="26" viewBox="0 0 24 24" fill="#000000" style="vertical-align: middle; margin-right: 4px;">
            <path d="M18.71 19.5c-.83 1.24-1.71 2.45-3.05 2.47-1.34.03-1.77-.79-3.29-.79-1.53 0-2 .77-3.27.82-1.31.05-2.3-1.32-3.14-2.53C4.25 17 2.94 12.45 4.7 9.39c.87-1.52 2.43-2.48 4.12-2.51 1.28-.02 2.5.87 3.29.87.78 0 2.26-1.07 3.81-.91.65.03 2.47.26 3.64 1.98-.09.06-2.17 1.28-2.15 3.81.03 3.02 2.65 4.03 2.68 4.04-.03.07-.42 1.44-1.38 2.83M15.97 6.37c.61-.75 1.04-1.8 1.01-2.87-.9.04-1.97.6-2.61 1.35-.57.66-.99 1.72-.94 2.76.99.08 1.93-.49 2.54-1.24z"/>
        </svg>
        <span>PriceIntelli</span>
    </div>
    """, unsafe_allow_html=True)

    nav_options = [
        "📊 Tổng quan (Dashboard)",
        "📱 Sản phẩm & So sánh giá (Products)",
        "⚡ Định giá động (Dynamic Pricing)",
        "🗄️ Quản lý dữ liệu (Data Management)",
        "📈 Báo cáo phân tích (Reports)",
        "🧠 Đánh giá mô hình AI (Model Insights)",
        "⚙️ Tự động hóa & Spiders (Automation)"
    ]

    selected_nav = st.radio(
        label="Menu điều hướng",
        options=nav_options,
        index=0,
        label_visibility="collapsed"
    )

    st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)

    # AI Assistant Drawer (Yêu cầu tài liệu mục 4)
    with st.expander("💬 Trợ lý AI PriceIntelli", expanded=False):
        st.caption("Hỏi đáp thông minh về giá sản phẩm, sàn rẻ nhất và xu hướng thị trường.")
        q_user = st.text_input("Nhập câu hỏi của bạn:", placeholder="Ví dụ: sản phẩm nào rẻ nhất?", key="sidebar_ai_q")
        if q_user:
            with st.spinner("Đang truy vấn dữ liệu dự án..."):
                ans = ask_assistant(q_user, df_products)
                st.write(ans)

    # Trạng thái đồng bộ dữ liệu & nút làm mới thủ công
    latest_dt = df_products["crawl_date"].max() if (not df_products.empty and "crawl_date" in df_products.columns) else "N/A"
    badge_bg = "#ECFDF5" if "PostgreSQL" in data_source else "#FEF3C7"
    badge_fg = "#059669" if "PostgreSQL" in data_source else "#B45309"
    dot_icon = "🟢" if "PostgreSQL" in data_source else "🟡"
    st.markdown(f"""
    <div style="margin-top: 16px; padding: 10px 12px; border-radius: 10px; background: {badge_bg}; color: {badge_fg}; font-size: 12px; font-weight: 600;">
        {dot_icon} {data_source}<br/>
        <span style="font-weight: 400;">Ngày mới nhất: {latest_dt} ({len(df_products)} SKUs)</span>
    </div>
    """, unsafe_allow_html=True)
    if st.button("🔄 Làm mới dữ liệu", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

# --- PAGE ROUTING ---
if "Tổng quan" in selected_nav:
    render_dashboard_view(df_products)
elif "Sản phẩm" in selected_nav:
    render_products_view(df_products)
elif "Định giá động" in selected_nav:
    render_pricing_view(df_products)
elif "Quản lý dữ liệu" in selected_nav:
    render_management_view(df_products)
elif "Báo cáo" in selected_nav:
    render_reports_view(df_products)
elif "Đánh giá mô hình" in selected_nav:
    render_insights_view(df_products)
elif "Tự động hóa" in selected_nav:
    render_automation_view(df_products)
