import re
import pandas as pd
import streamlit as st
from api_client import get_latest_products, get_price_forecast, predict_price_ml


def answer_user_query(query: str, df: pd.DataFrame) -> dict:
    """Xử lý câu hỏi ngôn ngữ tự nhiên thông minh theo đúng mục 4 trong tài liệu"""
    q = query.lower().strip()

    # 1. Tìm sản phẩm rẻ nhất
    if any(k in q for k in ["rẻ nhất", "cheapest", "giá thấp nhất", "gia re"]):
        top5 = df[df["price"] > 5000000].sort_values("price", ascending=True).head(5)
        cols = ["title", "store", "price"]
        if "listed_price" in top5.columns:
            cols.append("listed_price")
        return {
            "type": "dataframe",
            "message": "🏆 Top 5 sản phẩm iPhone có giá bán rẻ nhất thị trường hiện tại:",
            "data": top5[cols],
        }

    # 2. Sàn nào bán rẻ nhất / giá tốt nhất
    if any(k in q for k in ["sàn nào", "cửa hàng nào", "store nào", "ở đâu rẻ"]):
        summary = (
            df[df["price"] > 5000000]
            .groupby("store")["price"]
            .agg(Gia_TB="mean", Gia_Min="min", So_Luong="count")
            .reset_index()
            .sort_values("Gia_TB", ascending=True)
        )
        cheapest_store = summary.iloc[0]["store"]
        return {
            "type": "dataframe",
            "message": f"📊 Theo phân tích tổng hợp, **{cheapest_store}** hiện đang có mức giá trung bình rẻ nhất:",
            "data": summary,
        }

    # 3. Dự báo giá iPhone
    if any(k in q for k in ["dự báo", "forecast", "xu hướng giá", "tuần tới"]):
        match = re.search(r"(\d+)", q)
        gen = match.group(1) if match else "16"
        key = f"iphone-{gen}-pro-max-256gb"
        fc = get_price_forecast(key, days_ahead=14)
        trend = "giảm nhẹ (phù hợp để canh mua)" if fc.get("trend") == "down" else "tăng nhẹ"
        return {
            "type": "text",
            "message": f"📈 Dự báo giá cho **iPhone {gen}**: Trong 14 ngày tới xu hướng giá có chiều hướng **{trend}**. Bạn có thể xem chi tiết biểu đồ tại trang **3_Forecast**.",
        }

    # 4. Giảm giá sốc nhất / khuyến mãi nhiều nhất
    if any(k in q for k in ["giảm giá", "khuyến mãi", "sale", "discount", "sốc"]):
        if "discount_pct" in df.columns:
            top_sale = df.sort_values("discount_pct", ascending=False).head(5)
            return {
                "type": "dataframe",
                "message": "🔥 Top các sản phẩm đang được giảm giá sâu nhất so với niêm yết:",
                "data": top_sale[["title", "store", "price", "discount_pct"]],
            }

    # 5. So sánh giá model cụ thể
    match = re.search(r"iphone\s*(\d+)", q)
    if match:
        gen = match.group(1)
        sub = df[df["title"].str.contains(f"iPhone {gen}", case=False, na=False)]
        if not sub.empty:
            summary = sub.groupby("store")["price"].min().reset_index().sort_values("price")
            return {
                "type": "dataframe",
                "message": f"🔍 So sánh giá rẻ nhất cho **iPhone {gen}** tại các chuỗi cửa hàng:",
                "data": summary,
            }

    # Mặc định
    return {
        "type": "text",
        "message": (
            "🤖 Tôi có thể giải đáp các câu hỏi như:\n"
            "- *'Sản phẩm nào đang rẻ nhất?'*\n"
            "- *'Sàn nào có giá tốt nhất tuần này?'*\n"
            "- *'Dự báo giá iPhone 16 tuần tới'* \n"
            "- *'Top sản phẩm giảm giá sâu nhất'* \n"
            "- *'So sánh giá iPhone 15 giữa các sàn'*"
        ),
    }


# Alias for compatibility with course document specification (mục 4.3)
def ask_assistant(question: str, df: pd.DataFrame):
    res = answer_user_query(question, df)
    if res.get("type") == "dataframe":
        return res.get("data")
    return res.get("message")



def render_ai_assistant(df: pd.DataFrame):
    """Khung chat AI Assistant thông minh tương tác trực quan (mục 4 trong tài liệu)"""
    st.subheader("💬 Trợ lý AI Hỏi đáp Thị trường (PriceIntelli AI Assistant)")
    st.caption("Đặt câu hỏi bằng ngôn ngữ tự nhiên để truy vấn số liệu và nhận định thị trường tức thì.")

    # Khởi tạo lịch sử chat trong session_state
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {
                "role": "assistant",
                "content": "Xin chào! Tôi là Trợ lý AI PriceIntelli. Bạn cần tra cứu giá hoặc dự báo mẫu iPhone nào hôm nay?",
            }
        ]

    # Hiển thị các tin nhắn trước
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if "table" in msg and msg["table"] is not None:
                st.dataframe(msg["table"], use_container_width=True)

    # Nhận câu hỏi mới từ người dùng
    user_prompt = st.chat_input("Nhập câu hỏi của bạn (ví dụ: 'Sản phẩm nào rẻ nhất?', 'Dự báo giá iPhone 16')...")

    if user_prompt:
        # Lưu câu hỏi của người dùng
        st.session_state.messages.append({"role": "user", "content": user_prompt})
        with st.chat_message("user"):
            st.markdown(user_prompt)

        # Trả lời
        ans = answer_user_query(user_prompt, df)
        with st.chat_message("assistant"):
            st.markdown(ans["message"])
            table_data = None
            if ans["type"] == "dataframe":
                st.dataframe(ans["data"], use_container_width=True)
                table_data = ans["data"]

        st.session_state.messages.append({
            "role": "assistant",
            "content": ans["message"],
            "table": table_data,
        })
