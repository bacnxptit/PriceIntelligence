import streamlit as st


def render_alerts(alerts: list):
    """Hiển thị khối cảnh báo ở đầu dashboard theo đúng chuẩn mục 3 trong tài liệu"""
    if not alerts:
        st.success("✅ Hôm nay không có biến động giá bất thường nào từ đối thủ.")
        return

    st.subheader("🚨 Cảnh báo biến động giá thị trường (Price Alerts)")

    col1, col2 = st.columns([3, 1])
    with col1:
        severity_filter = st.selectbox(
            "Lọc mức độ nghiêm trọng:",
            options=["Tất cả", "Cao", "Trung bình", "Thấp"],
            index=0,
            key="alert_sev_filter",
        )
    with col2:
        mark_as_read = st.checkbox("Đánh dấu đã xem", value=False, key="alert_mark_read")

    if mark_as_read:
        st.caption("Đã ẩn các cảnh báo đã xem.")
        return

    filtered_alerts = alerts
    if severity_filter != "Tất cả":
        filtered_alerts = [a for a in alerts if a.get("severity") == severity_filter]

    if not filtered_alerts:
        st.info(f"Không có cảnh báo nào ở mức độ: {severity_filter}")
        return

    # Hiển thị tối đa 5 cảnh báo quan trọng nhất
    for item in filtered_alerts[:5]:
        sev = item.get("severity", "Thấp")
        msg = f"**{item['title']}** — {item['detail']}"
        if sev == "Cao":
            st.error(msg, icon="🚨")
        elif sev == "Trung bình":
            st.warning(msg, icon="⚠️")
        else:
            st.info(msg, icon="ℹ️")
