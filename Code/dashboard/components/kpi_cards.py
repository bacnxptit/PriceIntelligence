import streamlit as st


def render_kpis(kpi_data: dict, alert_count: int = 0, current_index: float = 100.0):
    """Hiển thị hàng thẻ chỉ số KPI tổng quan (mục 2.2 và 2.3 trong tài liệu)"""
    total_products = kpi_data.get("total_products", 0)
    total_stores = kpi_data.get("total_stores", 8)
    increased = kpi_data.get("increased_products", 0)
    decreased = kpi_data.get("decreased_products", 0)
    out_of_stock = kpi_data.get("out_of_stock", 0)

    st.markdown("### 📊 Chỉ số thị trường tổng hợp (Market KPIs)")
    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        st.metric(
            label="📱 Sản phẩm theo dõi",
            value=f"{total_products:,}",
            help="Tổng số lượng SKU iPhone được thu thập và phân tích từ các sàn.",
        )

    with col2:
        st.metric(
            label="🏪 Sàn thương mại",
            value=f"{total_stores} sàn",
            delta="Apple, FPT, TGDD...",
            delta_color="off",
            help="Số chuỗi bán lẻ lớn đang được giám sát giá.",
        )

    with col3:
        st.metric(
            label="🚨 Cảnh báo hôm nay",
            value=f"{alert_count}",
            delta=f"{alert_count} biến động" if alert_count > 0 else "Ổn định",
            delta_color="inverse",
            help="Số đợt điều chỉnh giá sốc (>10%) hoặc đối thủ đổi giá.",
        )

    with col4:
        st.metric(
            label="📈 Tăng / 📉 Giảm giá",
            value=f"{increased} / {decreased}",
            delta=f"-{decreased} đợt giảm",
            delta_color="normal",
            help="Tỷ lệ sản phẩm đang tăng giá hoặc áp dụng khuyến mãi giảm giá.",
        )

    with col5:
        st.metric(
            label="🏷️ Chỉ số giá (Index)",
            value=f"{current_index:.1f} pts",
            delta="+0.8%" if current_index >= 100 else "-1.2%",
            help="Chỉ số giá tổng hợp thị trường so với mốc cơ sở 100.",
        )
