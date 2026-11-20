# PriceIntelli Streamlit Dashboard

Giao diện tương tác người dùng cao cấp cho nền tảng PriceIntelli, xây dựng bằng **Streamlit** và **Plotly**, tuân thủ nghiêm ngặt theo các nguyên tắc thiết kế tại Buổi 8:
- **Nguyên tắc phân tầng thông tin:** Đặt cảnh báo và thẻ KPI quan trọng nhất ở trên đầu, dữ liệu chi tiết ở dưới.
- **Biểu đồ trực quan:**
  - Lịch sử giá đa nguồn (Line chart - màu sắc nhất quán theo từng sàn).
  - Tỷ trọng 6 nhóm vị thế giá (Pie chart).
  - So sánh giá sản phẩm cùng loại đa sàn với giá trung bình thị trường (Bar chart).
- **Trợ lý AI Assistant:** Chatbot xử lý câu hỏi ngôn ngữ tự nhiên tích hợp trực tiếp trên dashboard (`st.chat_message`, `st.chat_input`).
- **Dự báo giá & Định giá AI:** Tích hợp mô hình Machine Learning (XGBoost) định giá iPhone thông minh.
- **Giám sát & Tự động hóa:** Xem lịch sử pipeline và bấm nút kích hoạt ETL trực tiếp từ web.

---

## 1. Cấu trúc thư mục

```
dashboard/
├── app.py                   # Entrypoint chính của Streamlit (Bộ lọc toàn cục, Alerts, KPI, AI Chat)
├── api_client.py            # Client gọi FastAPI Backend (tự động fallback DB/CSV an toàn)
├── requirements.txt         # Khai báo các thư viện (streamlit, plotly, pandas...)
├── Dockerfile               # Đóng gói ứng dụng để deploy
├── components/
│   ├── alerts_box.py        # Hiển thị khối cảnh báo giá phân 3 cấp độ (Cao, Trung bình, Thấp)
│   ├── kpi_cards.py         # Hiển thị hàng thẻ chỉ số KPI tổng hợp
│   ├── charts.py            # Vẽ biểu đồ Plotly chuyên nghiệp (Price Index, Vị thế giá, So sánh)
│   └── ai_assistant.py      # Trợ lý AI hỏi đáp dữ liệu ngôn ngữ tự nhiên
└── pages/
    ├── 1_Overview.py        # Trang 1: Tổng quan thị trường & Top sản phẩm giảm giá
    ├── 2_Analytics.py       # Trang 2: Phân tích chuyên sâu & Chuỗi thời gian
    ├── 3_Forecast.py        # Trang 3: Dự báo xu hướng 14 ngày & Công cụ định giá AI
    └── 4_Automation.py      # Trang 4: Quản trị tự động hóa & Lịch sử chạy ETL
```

---

## 2. Hướng dẫn khởi động nhanh

### 2.1 Cài đặt dependencies (nếu chưa có)
```bash
pip install -r requirements.txt
```

### 2.2 Khởi động Dashboard
Chạy lệnh sau trong terminal:
```bash
streamlit run app.py
```
Hoặc từ thư mục gốc của dự án:
```bash
streamlit run Code/dashboard/app.py
```

Trình duyệt sẽ tự động mở tại: **`http://localhost:8501`**

---

## 3. Khởi động cùng Backend FastAPI (Tùy chọn)

Để khai thác tối đa hiệu năng và kết nối mạng đầy đủ giữa các thành phần:
1. **Terminal 1:** Khởi động Backend API
   ```bash
   cd Code/priceintelli-api
   uvicorn main:app --reload --port 8000
   ```
2. **Terminal 2:** Khởi động Dashboard
   ```bash
   cd Code/dashboard
   streamlit run app.py
   ```
*(Lưu ý: Nếu chưa bật Backend API, Dashboard vẫn tự động kích hoạt chế độ Fallback để hiển thị dữ liệu bình thường, không bao giờ bị lỗi màn hình trắng!)*
