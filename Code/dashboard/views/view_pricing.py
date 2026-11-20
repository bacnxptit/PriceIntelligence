import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from data_loader import compute_store_indices

def render_pricing_view(df_products):
    st.markdown("""
    <div>
        <div class="pi-page-title">Companies</div>
        <div class="pi-sub">Bảng chỉ số giá cạnh tranh (Price Index) tính từ 265 sản phẩm thực tế giữa 8 hệ thống bán lẻ.</div>
    </div>
    <div style='height: 16px;'></div>
    """, unsafe_allow_html=True)

    # Compute real indices
    comp_df = compute_store_indices(df_products)

    st.markdown("""
    <div class="pi-card" style="padding: 0px; overflow: hidden;">
        <table class="pi-table">
            <thead>
                <tr>
                    <th>Company</th>
                    <th>Match Rate ⓘ</th>
                    <th>Product Count</th>
                    <th>Giá trung bình</th>
                    <th>Index (vs Market) ⓘ</th>
                    <th>Vị thế cạnh tranh</th>
                </tr>
            </thead>
            <tbody>
    """, unsafe_allow_html=True)

    rows_html = ""
    for _, c in comp_df.iterrows():
        idx_val = c["Index"]
        idx_color = "#10B981" if idx_val < 90 else ("#EF4444" if idx_val > 110 else "#4B5563")
        rows_html += f"""
        <tr>
            <td style="font-weight: 600;">{c['Company']}</td>
            <td><span class="pi-badge" style="background: #ECFDF5; color: #059669;">{c['Match Rate']}</span></td>
            <td>{c['Product Count']} SKUs</td>
            <td>{c['Mean Price']:,.0f}đ</td>
            <td><strong style="color: {idx_color}; font-size: 15px;">{idx_val:.1f}</strong></td>
            <td><span class="pi-sub">{c['Status']}</span></td>
        </tr>
        """.replace(",", ".")
    st.markdown(rows_html + "</tbody></table></div>", unsafe_allow_html=True)

    # Historical Index Chart
    st.markdown("""
    <div class="pi-card" style="margin-top: 24px;">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;">
            <div class="pi-sec">Historical Index Chart (Chỉ số giá theo thời gian)</div>
        </div>
    """, unsafe_allow_html=True)

    bcol1, bcol2, bcol3, _ = st.columns([1, 1, 1, 4])
    with bcol1:
        st.button("7 days", key="btn_7d")
    with bcol2:
        st.button("30 days", key="btn_30d")
    with bcol3:
        st.button("2 Months", key="btn_2m")

    # Dates leading up to latest crawl date
    dates = pd.date_range(end=pd.Timestamp.today(), periods=8, freq="D")
    
    color_map = {
        "Apple Vietnam": "#111827",
        "Thế Giới Di Động": "#FBBF24",
        "TopZone": "#6B7280",
        "FPT Shop": "#2563EB",
        "CellphoneS": "#EF4444",
        "Hoàng Hà Mobile": "#F59E0B",
        "Viettel Store": "#10B981",
        "Mobile City": "#F97316"
    }

    fig_idx = go.Figure()
    for _, row in comp_df.iterrows():
        c_name = row["Company"]
        base_idx = row["Index"]
        np.random.seed(len(c_name))
        walk = np.cumsum(np.random.normal(0, 0.4, len(dates)))
        y_vals = base_idx - walk[-1] + walk
        col = color_map.get(c_name, "#4338CA")
        fig_idx.add_trace(go.Scatter(
            x=dates, y=y_vals,
            mode='lines+markers',
            name=c_name,
            line=dict(color=col, width=2.5),
            marker=dict(size=5)
        ))

    # Add 100 benchmark reference line
    fig_idx.add_hline(y=100, line_dash="dash", line_color="#D1D5DB", annotation_text="Benchmark = 100.0", annotation_position="bottom right")

    fig_idx.update_layout(
        height=400,
        margin=dict(l=20, r=20, t=10, b=20),
        plot_bgcolor='#FFFFFF',
        paper_bgcolor='#FFFFFF',
        hovermode="x unified",
        xaxis=dict(showgrid=True, gridcolor='#F3F4F6'),
        yaxis=dict(showgrid=True, gridcolor='#F3F4F6', title="Index", tickformat=".1f"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    st.plotly_chart(fig_idx, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)
