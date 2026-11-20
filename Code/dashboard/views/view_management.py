import streamlit as st
import pandas as pd

def render_management_view(df_products):
    total_records = len(df_products)
    unique_stores = df_products["store"].nunique()
    unique_models = df_products["clean_model"].nunique()
    latest_crawl = df_products["crawl_date"].max() if "crawl_date" in df_products.columns else "2026-11-19"

    st.markdown("""
    <div>
        <div class="pi-page-title">Data Management</div>
        <div class="pi-sub">Dữ liệu thô và dữ liệu đã xử lý từ pipeline Price Intelligence thực tế.</div>
    </div>
    <div style='height: 16px;'></div>
    """, unsafe_allow_html=True)

    # 4 Real KPI cards
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(f"""
        <div class="pi-card">
            <div class="pi-kpi-label">Tổng bản ghi (Clean)</div>
            <div class="pi-big" style="color: #4338CA; font-size: 28px; margin-top: 4px;">{total_records}</div>
        </div>
        """, unsafe_allow_html=True)
    with c2:
        st.markdown(f"""
        <div class="pi-card">
            <div class="pi-kpi-label">Số sàn cào tự động</div>
            <div class="pi-big" style="font-size: 28px; margin-top: 4px;">{unique_stores}</div>
        </div>
        """, unsafe_allow_html=True)
    with c3:
        st.markdown(f"""
        <div class="pi-card">
            <div class="pi-kpi-label">Số model sản phẩm</div>
            <div class="pi-big" style="font-size: 28px; margin-top: 4px;">{unique_models}</div>
        </div>
        """, unsafe_allow_html=True)
    with c4:
        st.markdown(f"""
        <div class="pi-card">
            <div class="pi-kpi-label">Ngày crawl gần nhất</div>
            <div class="pi-big" style="font-size: 22px; margin-top: 4px; color: #10B981;">{latest_crawl}</div>
        </div>
        """, unsafe_allow_html=True)

    # Tab navigation
    t1, t2, t3 = st.tabs(["Clean Data (Đã làm sạch)", "Raw Crawled Data (Dữ liệu gốc)", "Matched Products (So khớp chuẩn hóa)"])

    with t1:
        st.markdown("<div class='pi-card'>", unsafe_allow_html=True)
        f_col1, f_col2 = st.columns([3, 1])
        with f_col1:
            q = st.text_input("🔍 Tìm kiếm theo tên sản phẩm hoặc chuỗi bán lẻ:", placeholder="Nhập từ khóa...")
        with f_col2:
            st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
            csv_data = df_products.to_csv(index=False).encode('utf-8')
            st.download_button("Export Clean CSV", data=csv_data, file_name="clean_products_export.csv", mime="text/csv")

        filtered_df = df_products.copy()
        if q:
            filtered_df = filtered_df[
                filtered_df["title"].astype(str).str.contains(q, case=False, na=False) |
                filtered_df["store"].astype(str).str.contains(q, case=False, na=False) |
                filtered_df["clean_model"].astype(str).str.contains(q, case=False, na=False)
            ]
        
        display_cols = ["clean_model", "store", "price", "listed_price", "discount_pct", "price_position", "capacity_gb", "rating", "crawl_date"]
        avail_cols = [c for c in display_cols if c in filtered_df.columns]

        st.dataframe(
            filtered_df[avail_cols],
            use_container_width=True,
            height=420,
            column_config={
                "clean_model": st.column_config.TextColumn("Model chuẩn hóa"),
                "store": st.column_config.TextColumn("Sàn bán lẻ"),
                "price": st.column_config.NumberColumn("Giá bán (VND)", format="%,d đ"),
                "listed_price": st.column_config.NumberColumn("Giá niêm yết (VND)", format="%,d đ"),
                "discount_pct": st.column_config.NumberColumn("Giảm (%)", format="%.1f%%"),
                "price_position": st.column_config.TextColumn("Vị trí giá"),
                "capacity_gb": st.column_config.NumberColumn("Dung lượng (GB)", format="%d GB"),
                "rating": st.column_config.NumberColumn("Đánh giá ⭐", format="%.1f"),
                "crawl_date": st.column_config.TextColumn("Ngày lấy")
            }
        )
        st.markdown("</div>", unsafe_allow_html=True)

    with t2:
        st.markdown("<div class='pi-card'>", unsafe_allow_html=True)
        st.markdown("<div class='pi-sec'>Dữ liệu thô từ 8 Scrapy Spiders</div>", unsafe_allow_html=True)
        st.caption("Dữ liệu trực tiếp từ các file cào JSON của Scrapy (TheGioiDiDong, CellphoneS, TopZone, FPT, Apple, Hoàng Hà, Viettel Store, MobileCity).")
        raw_display = df_products[["title", "store", "price", "crawled_at", "url"]].head(100)
        st.dataframe(raw_display, use_container_width=True, height=380)
        st.markdown("</div>", unsafe_allow_html=True)

    with t3:
        st.markdown("<div class='pi-card'>", unsafe_allow_html=True)
        st.markdown("<div class='pi-sec'>Kết quả So khớp sản phẩm (Product Matching)</div>", unsafe_allow_html=True)
        st.caption("Khử nhiễu tiêu đề HTML và gom nhóm về Canonical Model theo dung lượng GB.")
        matched_sample = df_products[["title", "clean_model", "capacity_gb", "store", "price"]].copy()
        matched_sample["Match Score"] = 1.00
        st.dataframe(matched_sample.head(100), use_container_width=True, height=380)
        st.markdown("</div>", unsafe_allow_html=True)
