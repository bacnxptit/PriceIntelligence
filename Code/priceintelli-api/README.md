# PriceIntelli Backend API (FastAPI)

Hệ thống Backend RESTful API hiệu năng cao cho dự án PriceIntelli, xây dựng bằng **FastAPI**, kết nối trực tiếp với **PostgreSQL (Supabase)**, **Scrapyd (Scrapy Crawler Controller)**, **ETL Pipeline Script** và **Mô hình Machine Learning (XGBoost / Gradient Boosting)**.

---

## 1. Cấu trúc thư mục

```
priceintelli-api/
├── main.py                  # Entrypoint chính của FastAPI (khởi tạo app, middleware, routes)
├── .env                     # File cấu hình biến môi trường
├── requirements.txt         # Thư viện phụ thuộc
├── api/
│   ├── __init__.py
│   ├── db.py                # Layer kết nối CSDL PostgreSQL Supabase qua psycopg & pandas
│   ├── read_products.py     # Nhóm API đọc dữ liệu sản phẩm & so sánh giá giữa các sàn
│   ├── read_timeseries.py   # Nhóm API phân tích chuỗi thời gian & chỉ số giá (Price Index)
│   ├── read_kpi.py          # Nhóm API thống kê KPI Dashboard, ma trận tương quan
│   ├── write.py             # Nhóm API lọc động nâng cao (Dynamic Filter) & xuất CSV
│   ├── analytics.py         # Nhóm API dự báo giá (14-day 95% CI) & phát hiện bất thường (Z-score)
│   ├── pipeline_audit.py    # Nhóm API giám sát và ghi nhật ký lịch sử chạy ETL
│   ├── scrapyd_client.py    # Nhóm API kết nối & điều khiển Scrapyd daemon (port 6800)
│   ├── etl_trigger.py       # Nhóm API kích hoạt chạy ETL script và Full Pipeline
│   └── ml_model.py          # Nhóm API tải mô hình XGBoost dự đoán giá & Feature Importance
├── models/
│   ├── xgboost_price.pkl    # Mô hình ML đã huấn luyện
│   └── metrics.json         # Đánh giá chỉ số mô hình (R2, MAE, RMSE)
└── logs/                    # Thư mục lưu log vận hành
```

---

## 2. Hướng dẫn cài đặt & Khởi động

### 2.1 Cài đặt thư viện
```bash
pip install -r requirements.txt
```

### 2.2 Cấu hình môi trường (.env)
File `.env` đã được chuẩn bị sẵn:
```env
POSTGRES_URL=postgresql://postgres.kvslwmjsulnolozinxyj:Gr%254TUYgu8%24kd%26%40@aws-0-ap-southeast-1.pooler.supabase.com:6543/postgres
PGSSLMODE=require
SCRAPYD_URL=http://127.0.0.1:6800
ETL_SCRIPT_PATH=../priceintelli-etl/etl_pipeline.py
ANALYTICS_SCRIPT_PATH=../MatchingData/bai5_price_analytics.py
ML_MODEL_PATH=models/xgboost_price.pkl
```

### 2.3 Khởi động Server
* **Chế độ phát triển (Development với Hot-reload):**
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```
* **Chế độ vận hành (Production đa luồng):**
```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

### 2.4 Truy cập API Docs
* **Swagger UI:** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs) (Thử nghiệm trực quan tất cả 37 API)
* **ReDoc:** [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

---

## 3. Danh sách các nhóm API chính

| Nhóm API | Prefix | Số endpoint | Mô tả |
| :--- | :--- | :---: | :--- |
| **Products** | `/api/products` | 6 | Lấy iPhone mới nhất, phân tích giá, lọc theo sàn, so sánh chênh lệch giá |
| **Time Series** | `/api/timeseries` | 3 | Chỉ số biến động giá (Price Index), lịch sử giá theo ngày, Min/Max/Avg |
| **KPI** | `/api/kpi` | 4 | KPI thẻ số liệu Dashboard, đếm vị thế giá, tỷ lệ match sàn, ma trận tương quan |
| **Write/Filter** | `/api/write` | 2 | Bộ lọc đa điều kiện động trên SQL và xuất toàn bộ dữ liệu ra CSV |
| **Analytics** | `/api/analytics` | 2 | Dự báo giá 14 ngày tới (hồi quy 95% CI) và phát hiện giá bất thường (Z-score) |
| **Pipeline** | `/api/pipeline` | 3 | Lịch sử chạy ETL (`/runs`), ghi log (`/log`), thống kê bản ghi theo ngày |
| **Scrapyd** | `/api/scrapyd` | 6 | Lập lịch cào (`/schedule`), hủy job (`/cancel`), xem danh sách spider & jobs |
| **ETL Trigger** | `/api/etl` | 3 | Kích hoạt ETL script (`/run`), chạy phân tích, chạy toàn chuỗi (`/full-pipeline`) |
| **ML Model** | `/api/ml` | 3 | Dự đoán giá iPhone (`/predict`), Feature Importance, chỉ số đánh giá (`/metrics`) |
