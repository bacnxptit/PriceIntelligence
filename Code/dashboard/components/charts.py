import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# Bảng màu cố định cho từng sàn (nhất quán giữa các biểu đồ theo mục 2.6)
STORE_COLORS = {
    "Apple Vietnam": "#000000",
    "FPT Shop": "#E31837",
    "The Gioi Di Dong": "#FFD400",
    "TopZone": "#0071E3",
    "CellphoneS": "#D70018",
    "Hoang Ha Mobile": "#008848",
    "Viettel Store": "#EE0033",
    "Mobile City": "#FF6600",
}


def plot_price_over_time(df_ts: pd.DataFrame):
    """Biểu đồ đường: Lịch sử giá theo thời gian, mỗi nguồn một đường (mục 2.4)"""
    if df_ts.empty:
        st.info("Chưa có đủ dữ liệu lịch sử giá.")
        return

    fig = px.line(
        df_ts,
        x="crawl_date",
        y="price_index",
        color="store",
        color_discrete_map=STORE_COLORS,
        title="Chỉ số giá theo thời gian giữa các sàn (Price Index over time)",
        labels={"crawl_date": "Ngày", "price_index": "Chỉ số giá (Base = 100)", "store": "Sàn bán lẻ"},
    )
    fig.update_layout(
        hovermode="x unified",
        margin=dict(l=20, r=20, t=50, b=20),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    st.plotly_chart(fig, use_container_width=True)


def plot_price_position(df_pos: pd.DataFrame):
    """Biểu đồ tròn / Donut: Tỷ trọng 6 nhóm vị thế giá (mục 2.4 & 2.6)"""
    if df_pos.empty:
        st.info("Chưa có dữ liệu vị thế giá.")
        return

    fig = px.pie(
        df_pos,
        names="price_position",
        values="count",
        title="Tỷ trọng vị thế giá trên thị trường (Price Position Distribution)",
        hole=0.45,
        color_discrete_sequence=px.colors.sequential.RdBu,
    )
    fig.update_traces(textposition="inside", textinfo="percent+label")
    fig.update_layout(margin=dict(l=20, r=20, t=50, b=20))
    st.plotly_chart(fig, use_container_width=True)


def plot_store_comparison(df_products: pd.DataFrame, model_name: str = None):
    """Biểu đồ cột: So sánh giá cùng một model giữa các sàn bán lẻ"""
    if df_products.empty:
        return

    sub_df = df_products
    if model_name:
        sub_df = df_products[df_products["title"].str.contains(model_name, case=False, na=False)]

    if sub_df.empty:
        sub_df = df_products.head(10)

    # Lấy giá rẻ nhất theo từng sàn cho model này
    summary = (
        sub_df.groupby("store")["price"]
        .min()
        .reset_index()
        .sort_values("price", ascending=True)
    )

    avg_price = summary["price"].mean()

    fig = px.bar(
        summary,
        x="store",
        y="price",
        color="store",
        color_discrete_map=STORE_COLORS,
        title=f"So sánh giá bán thực tế theo sàn: {model_name or 'iPhone'}",
        labels={"store": "Cửa hàng / Sàn", "price": "Giá bán (VND)"},
        text_auto=".2s",
    )
    # Thêm đường kẻ giá trung bình thị trường
    fig.add_hline(
        y=avg_price,
        line_dash="dot",
        annotation_text=f"Trung bình thị trường: {avg_price:,.0f} đ",
        annotation_position="top left",
        line_color="gray",
    )
    fig.update_layout(margin=dict(l=20, r=20, t=50, b=20), showlegend=False)
    st.plotly_chart(fig, use_container_width=True)


def plot_forecast_curve(forecast_data: dict):
    """Biểu đồ dự báo giá 14 ngày tới kèm khoảng tin cậy 95% Confidence Interval"""
    if not forecast_data or "forecast" not in forecast_data:
        st.info("Không có dữ liệu dự báo.")
        return

    hist = forecast_data.get("history", {})
    fc = forecast_data.get("forecast", {})

    hist_dates = pd.to_datetime(hist.get("dates", []))
    hist_prices = hist.get("prices", [])

    fc_dates = pd.to_datetime(fc.get("dates", []))
    fc_prices = fc.get("prices", [])
    lower = fc.get("lower", [])
    upper = fc.get("upper", [])

    fig = go.Figure()

    # Đường giá quá khứ
    fig.add_trace(
        go.Scatter(
            x=hist_dates,
            y=hist_prices,
            mode="lines+markers",
            name="Lịch sử giá thực tế",
            line=dict(color="#0071E3", width=2),
        )
    )

    # Dải khoảng tin cậy 95% (Confidence Interval)
    fig.add_trace(
        go.Scatter(
            x=list(fc_dates) + list(fc_dates[::-1]),
            y=list(upper) + list(lower[::-1]),
            fill="toself",
            fillcolor="rgba(0, 113, 227, 0.15)",
            line=dict(color="rgba(255,255,255,0)"),
            hoverinfo="skip",
            showlegend=True,
            name="Khoảng tin cậy 95% CI",
        )
    )

    # Đường giá dự báo
    fig.add_trace(
        go.Scatter(
            x=fc_dates,
            y=fc_prices,
            mode="lines+markers",
            name="Giá dự báo (Forecast)",
            line=dict(color="#FF6600", width=3, dash="dash"),
        )
    )

    trend = forecast_data.get("trend", "down")
    trend_txt = "Xu hướng: 📈 TĂNG GIÁ" if trend == "up" else "Xu hướng: 📉 GIẢM GIÁ (Khuyến nghị chờ mua)"

    fig.update_layout(
        title=f"Dự báo xu hướng giá 14 ngày tới ({trend_txt})",
        xaxis_title="Thời gian",
        yaxis_title="Giá bán dự kiến (VND)",
        hovermode="x unified",
        margin=dict(l=20, r=20, t=50, b=20),
    )
    st.plotly_chart(fig, use_container_width=True)
