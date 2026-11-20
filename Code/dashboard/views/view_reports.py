import streamlit as st
import pandas as pd
import plotly.express as px

def render_reports_view(df_products):
    st.markdown("""
    <div>
        <div class="pi-page-title">Reports</div>
        <div class="pi-sub">Báo cáo tổng hợp thị trường giá bán lẻ theo phân khúc thế hệ và thương hiệu từ dữ liệu thật.</div>
    </div>
    <div style='height: 16px;'></div>
    """, unsafe_allow_html=True)

    t1, t2, t3 = st.tabs(["Category Reports (Theo thế hệ iPhone)", "Brand Reports (Độ phủ thương hiệu)", "Export Reports (Xuất báo cáo)"])

    with t1:
        st.markdown("""
        <div class="pi-card">
            <div class="pi-sec">Giá trung bình theo thế hệ iPhone (Dữ liệu thực tế)</div>
            <div class="pi-sec-sub">Thống kê giá trung bình từ 265 sản phẩm theo từng thế hệ iPhone 13, 14, 15, 16, 17, 18.</div>
        """, unsafe_allow_html=True)

        # Real aggregation by generation
        gen_df = df_products[df_products["generation"] > 0].copy()
        gen_stats = gen_df.groupby("generation")["price"].agg(["count", "mean", "min", "max"]).reset_index()
        gen_stats["Dòng máy"] = gen_stats["generation"].apply(lambda g: f"iPhone {g}")
        gen_stats = gen_stats.sort_values("generation", ascending=True)

        fig_rep = px.bar(
            gen_stats, x="Dòng máy", y="mean",
            text=gen_stats["mean"].apply(lambda v: f"{v:,.0f}đ".replace(",", ".")),
            color="mean",
            color_continuous_scale=[[0, "#EEF2FF"], [1, "#4338CA"]]
        )
        fig_rep.update_traces(textposition='outside')
        fig_rep.update_layout(
            height=340,
            margin=dict(l=20, r=20, t=20, b=20),
            plot_bgcolor='#FFFFFF',
            paper_bgcolor='#FFFFFF',
            coloraxis_showscale=False,
            xaxis=dict(title=""),
            yaxis=dict(title="Giá trung bình (VND)", tickformat=",.0f", range=[0, gen_stats["mean"].max() * 1.2], showgrid=True, gridcolor='#F3F4F6')
        )
        st.plotly_chart(fig_rep, use_container_width=True)

        st.markdown("#### Bảng thống kê chi tiết theo thế hệ")
        table_gen = gen_stats[["Dòng máy", "count", "min", "mean", "max"]].rename(columns={
            "count": "Số lượng SKU",
            "min": "Giá thấp nhất",
            "mean": "Giá trung bình",
            "max": "Giá cao nhất"
        })
        st.dataframe(
            table_gen,
            use_container_width=True,
            column_config={
                "Số lượng SKU": st.column_config.NumberColumn(format="%d"),
                "Giá thấp nhất": st.column_config.NumberColumn(format="%,d đ"),
                "Giá trung bình": st.column_config.NumberColumn(format="%,d đ"),
                "Giá cao nhất": st.column_config.NumberColumn(format="%,d đ")
            }
        )
        st.markdown("</div>", unsafe_allow_html=True)

    with t2:
        st.markdown("""
        <div class="pi-card">
            <div class="pi-sec">Brand Reports — Thị phần & Độ phủ tại 8 hệ thống bán lẻ</div>
            <div class="pi-sec-sub">Phân bố số lượng sản phẩm Apple trên từng chuỗi cửa hàng trong dự án.</div>
        """, unsafe_allow_html=True)
        store_counts = df_products["store"].value_counts().reset_index()
        store_counts.columns = ["Hệ thống bán lẻ", "Số lượng sản phẩm"]
        
        fig_store_share = px.bar(
            store_counts, x="Hệ thống bán lẻ", y="Số lượng sản phẩm",
            text="Số lượng sản phẩm",
            color="Số lượng sản phẩm",
            color_continuous_scale=[[0, "#EEF2FF"], [1, "#4338CA"]]
        )
        fig_store_share.update_traces(textposition='outside')
        fig_store_share.update_layout(
            height=300,
            margin=dict(l=20, r=20, t=20, b=20),
            plot_bgcolor='#FFFFFF',
            paper_bgcolor='#FFFFFF',
            coloraxis_showscale=False,
            xaxis=dict(title=""),
            yaxis=dict(title="Số SKU", showgrid=True, gridcolor='#F3F4F6')
        )
        st.plotly_chart(fig_store_share, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with t3:
        st.markdown("""
        <div class="pi-card">
            <div class="pi-sec">Export Reports</div>
            <div class="pi-sec-sub">Xuất toàn bộ tập dữ liệu đã làm sạch hoặc báo cáo theo model.</div>
        """, unsafe_allow_html=True)
        rep_csv = df_products.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Tải dữ liệu toàn bộ sản phẩm (CSV)", data=rep_csv, file_name="price_intelligence_full_report.csv", mime="text/csv")
        st.markdown("</div>", unsafe_allow_html=True)
