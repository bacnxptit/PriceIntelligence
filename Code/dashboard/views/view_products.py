import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

def render_products_view(df_products):
    total_found = len(df_products)
    all_models = df_products["clean_model"].value_counts().index.tolist()

    # Header
    col_t1, col_t2 = st.columns([3, 1])
    with col_t1:
        st.markdown(f"""
        <div>
            <div class="pi-page-title">Products</div>
            <div class="pi-sub">{total_found} bản ghi sản phẩm từ 8 sàn bán lẻ.</div>
        </div>
        """, unsafe_allow_html=True)
    with col_t2:
        b1, b2, b3 = st.columns(3)
        with b1:
            st.button("Manage")
        with b2:
            csv_data = df_products.to_csv(index=False).encode('utf-8')
            st.download_button("Export", data=csv_data, file_name="products_export.csv", mime="text/csv")
        with b3:
            st.button("Import")

    st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

    # Main Comparison Card
    st.markdown("""
    <div class="pi-card">
        <div class="pi-sec">So sánh giá iPhone thực tế giữa các sàn</div>
        <div class="pi-sec-sub">Chọn một model để xem toàn bộ sàn bán lẻ đang bán giá bao nhiêu từ dữ liệu cào thực tế.</div>
    """, unsafe_allow_html=True)

    selected_model = st.selectbox("Chọn model phân tích:", all_models, index=0)

    # Filter data for this model
    sub = df_products[df_products["clean_model"] == selected_model].sort_values("price", ascending=True)

    p_min = sub["price"].min()
    p_mean = sub["price"].mean()
    p_max = sub["price"].max()
    p_diff = p_max - p_min
    p_diff_pct = (p_diff / p_min * 100) if p_min > 0 else 0

    # 4 metrics calculated dynamically
    mcol1, mcol2, mcol3, mcol4 = st.columns(4)
    with mcol1:
        st.markdown(f"<div style='font-size: 13px; color: #6B7280;'>Thấp nhất</div><div style='font-size: 18px; font-weight: 700; color: #10B981;'>{p_min:,.0f}đ</div>".replace(",", "."), unsafe_allow_html=True)
    with mcol2:
        st.markdown(f"<div style='font-size: 13px; color: #6B7280;'>Trung bình</div><div style='font-size: 18px; font-weight: 700; color: #111827;'>{p_mean:,.0f}đ</div>".replace(",", "."), unsafe_allow_html=True)
    with mcol3:
        st.markdown(f"<div style='font-size: 13px; color: #6B7280;'>Cao nhất</div><div style='font-size: 18px; font-weight: 700; color: #EF4444;'>{p_max:,.0f}đ</div>".replace(",", "."), unsafe_allow_html=True)
    with mcol4:
        st.markdown(f"<div style='font-size: 13px; color: #6B7280;'>Chênh lệch</div><div style='font-size: 18px; font-weight: 700; color: #4338CA;'>{p_diff:,.0f}đ <span style='font-size: 13px; font-weight: 500;'>({p_diff_pct:.1f}%)</span></div>".replace(",", "."), unsafe_allow_html=True)

    # Real Bar chart across stores selling this model
    store_price_agg = sub.groupby("store")["price"].min().reset_index().sort_values("price", ascending=True)

    fig_store = px.bar(
        store_price_agg, x="store", y="price",
        text=store_price_agg["price"].apply(lambda p: f"{p:,.0f}đ".replace(",", ".")),
        color="price",
        color_continuous_scale=[[0, "#EEF2FF"], [1, "#4338CA"]]
    )
    fig_store.update_traces(textposition='outside')
    fig_store.update_layout(
        height=320,
        margin=dict(l=20, r=20, t=20, b=20),
        plot_bgcolor='#FFFFFF',
        paper_bgcolor='#FFFFFF',
        coloraxis_showscale=False,
        xaxis=dict(title=""),
        yaxis=dict(title="Giá (VND)", tickformat=",.0f", range=[0, p_max * 1.15], showgrid=True, gridcolor='#F3F4F6')
    )
    st.plotly_chart(fig_store, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

    # Filter Bar
    st.markdown("""
    <div class="pi-card" style="padding: 14px 20px;">
        <div style="display: flex; align-items: center; justify-content: space-between;">
            <div style="display: flex; align-items: center; gap: 14px;">
                <span style="font-weight: 600; font-size: 14px; color: #111827;">Bộ lọc</span>
                <span class="pi-badge" style="background: #EEF2FF; color: #4338CA;">● PRODUCT (Apple iPhone)</span>
                <span class="pi-badge">● 8 RETAIL STORES</span>
            </div>
            <div style="display: flex; gap: 8px;">
                <span style="font-size: 13px; color: #4338CA; cursor: pointer; padding: 6px 12px; font-weight: 600;">+ Bộ lọc mới</span>
                <span style="font-size: 13px; color: #6B7280; cursor: pointer; padding: 6px 12px;">Reset filter</span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # 2 Mini Cards Row
    k1, k2 = st.columns(2)
    disc_sub = (sub["discount_pct"] > 0).sum()
    full_sub = len(sub) - disc_sub

    with k1:
        st.markdown(f"""
        <div class="pi-card">
            <div class="pi-card-title"><span style="color: #4338CA;">🏷</span> Price Changes ({selected_model})</div>
            <div class="pi-kpi-row">
                <span class="pi-kpi-label">↑ Giữ giá / Giá gốc</span>
                <span class="pi-kpi-value green">{full_sub} Bản ghi</span>
            </div>
            <div class="pi-kpi-row">
                <span class="pi-kpi-label">↓ Giảm giá / Khuyến mãi</span>
                <span class="pi-kpi-value red">{disc_sub} Bản ghi</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
    with k2:
        st.markdown(f"""
        <div class="pi-card">
            <div class="pi-card-title"><span style="color: #4338CA;">📦</span> Hiện diện tại các hệ thống</div>
            <div class="pi-kpi-row">
                <span class="pi-kpi-label">Số sàn có hàng</span>
                <span class="pi-kpi-value muted">{sub['store'].nunique()} / 8 Hệ thống</span>
            </div>
            <div class="pi-kpi-row">
                <span class="pi-kpi-label">Tổng số phiên bản chào bán</span>
                <span class="pi-kpi-value green">{len(sub)} SKU</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # Selected Model Details Card
    st.markdown(f"""
    <div class="pi-card">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
            <div style="font-size: 18px; font-weight: 700; color: #111827;">{selected_model}</div>
            <div style="color: #6B7280; font-size: 13px;">Chi tiết thị trường &nbsp;&nbsp; ☆ &nbsp;&nbsp; ⋮</div>
        </div>
        <div style="display: flex; gap: 12px; margin-bottom: 14px;">
            <span class="pi-badge">Brand: Apple</span>
            <span class="pi-badge">Category: Điện thoại (Smartphones)</span>
            <span class="pi-badge">Số sàn có bán: {sub['store'].nunique()} / 8</span>
        </div>
        <div style="display: flex; gap: 24px; font-size: 14px; margin-bottom: 16px;">
            <div>Giá thấp nhất: <strong style="color: #10B981;">{p_min:,.0f}đ</strong></div>
            <div>Giá cao nhất: <strong style="color: #EF4444;">{p_max:,.0f}đ</strong></div>
            <div>Chênh lệch: <strong style="color: #4338CA;">{p_diff:,.0f}đ ({p_diff_pct:.1f}%)</strong></div>
        </div>
    """.replace(",", "."), unsafe_allow_html=True)

    det_col1, det_col2 = st.columns(2)
    with det_col1:
        st.markdown("<div style='font-size: 14px; font-weight: 600; color: #111827; margin-bottom: 8px;'>📈 Bảng giá chi tiết từng sàn</div>", unsafe_allow_html=True)
        st.dataframe(
            sub[["store", "price", "listed_price", "discount_pct"]].rename(columns={
                "store": "Hệ thống bán lẻ",
                "price": "Giá bán (VND)",
                "listed_price": "Giá niêm yết (VND)",
                "discount_pct": "Giảm (%)"
            }),
            use_container_width=True,
            height=200,
            column_config={
                "Giá bán (VND)": st.column_config.NumberColumn(format="%,d đ"),
                "Giá niêm yết (VND)": st.column_config.NumberColumn(format="%,d đ"),
                "Giảm (%)": st.column_config.NumberColumn(format="%.1f%%")
            }
        )

    with det_col2:
        st.markdown(f"<div style='font-size: 14px; font-weight: 600; color: #111827; margin-bottom: 8px;'>Phân bổ giá — {selected_model}</div>", unsafe_allow_html=True)
        fig_dist = px.histogram(
            sub, x="price", nbins=6,
            color_discrete_sequence=['#4338CA']
        )
        fig_dist.update_layout(
            height=200,
            margin=dict(l=10, r=10, t=10, b=10),
            plot_bgcolor='#FFFFFF',
            paper_bgcolor='#FFFFFF',
            xaxis=dict(title="Giá (VND)", tickformat=",.0f"),
            yaxis=dict(title="Số SKU", showgrid=True, gridcolor='#F3F4F6')
        )
        st.plotly_chart(fig_dist, use_container_width=True)
        median_p = sub["price"].median()
        st.markdown(f"<div style='font-size: 12px; color: #6B7280; text-align: right;'>Mean: {p_mean:,.0f}đ &nbsp;|&nbsp; Median: {median_p:,.0f}đ</div>".replace(",", "."), unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)
