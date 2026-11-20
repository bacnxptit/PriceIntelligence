import json
import os
import re
import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_CSV_PATH = os.path.abspath(os.path.join(BASE_DIR, "..", "CleanData", "clean_products.csv"))
MODEL_OUTPUT_DIR = os.path.join(BASE_DIR, "models")
os.makedirs(MODEL_OUTPUT_DIR, exist_ok=True)


def extract_features(df: pd.DataFrame) -> pd.DataFrame:
    """Trích xuất các đặc trưng đầu vào phục vụ huấn luyện mô hình dự đoán giá"""

    def extract_generation(title):
        m = re.search(r"iphone\s*(\d+)", str(title), re.IGNORECASE)
        return int(m.group(1)) if m else 15

    df = df.copy()
    df["generation"] = df["title"].apply(extract_generation)
    df["is_pro"] = df["title"].str.contains("pro", case=False).astype(int)
    df["is_promax"] = df["title"].str.contains("pro max", case=False).astype(int)
    df["is_plus"] = df["title"].str.contains("plus", case=False).astype(int)
    df["capacity_gb"] = df["capacity_gb"].fillna(128).astype(int)
    df["rating"] = df["rating"].fillna(5.0).astype(float)
    df["reviews"] = df["reviews"].fillna(0).astype(int)
    return df


def train():
    print("=" * 60)
    print("BAT DAU HUAN LUYEN MO HINH DU DOAN GIA IPHONE (XGBOOST / GBDT)")
    print("=" * 60)

    # 1. Doc du lieu tu CSV da lam sach
    if not os.path.exists(DATA_CSV_PATH):
        raise FileNotFoundError(f"Khong tim thay tap du lieu tai: {DATA_CSV_PATH}")

    df = pd.read_csv(DATA_CSV_PATH)
    print(f"[Data] Da doc {len(df)} ban ghi tu {DATA_CSV_PATH}")

    # 2. Trich chon dac trung & loc gia hop le (> 5 trieu)
    df_feat = extract_features(df)
    df_valid = df_feat[df_feat["price"] > 5000000].copy()
    print(f"[Features] {len(df_valid)} mau hop le duoc dua vao huan luyen")

    feature_cols = ["generation", "capacity_gb", "is_pro", "is_promax", "is_plus", "rating", "reviews"]
    X = df_valid[feature_cols]
    y = df_valid["price"]

    # 3. Chia tap Train / Test
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # 4. Huan luyen Gradient Boosting Regressor (Tuong duong XGBoost)
    model = GradientBoostingRegressor(
        n_estimators=100,
        learning_rate=0.1,
        max_depth=4,
        random_state=42,
    )
    model.fit(X_train, y_train)

    # 5. Danh gia do chinh xac tren tap Test
    y_pred = model.predict(X_test)
    r2 = r2_score(y_test, y_pred)
    mae = mean_absolute_error(y_test, y_pred)
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))

    print(f"[Metrics] R2 Score: {r2:.4f}")
    print(f"[Metrics] MAE (Sai so trung binh): {mae:,.0f} VND")
    print(f"[Metrics] RMSE: {rmse:,.0f} VND")

    # 6. Luu mo hinh va metadata
    model_path = os.path.join(MODEL_OUTPUT_DIR, "xgboost_price.pkl")
    joblib.dump(model, model_path)
    print(f"[Save] Da luu mo hinh vao: {model_path}")

    metrics = {
        "model_name": "GradientBoostingRegressor (XGBoost)",
        "dataset_source": DATA_CSV_PATH,
        "total_samples": len(df_valid),
        "r2_score": round(float(r2), 4),
        "mae": round(float(mae), 0),
        "rmse": round(float(rmse), 0),
        "features": feature_cols,
        "feature_importances": {
            feat: round(float(imp), 4)
            for feat, imp in zip(feature_cols, model.feature_importances_)
        },
    }

    metrics_path = os.path.join(MODEL_OUTPUT_DIR, "metrics.json")
    with open(metrics_path, "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2, ensure_ascii=False)
    print(f"[Save] Da luu metrics vao: {metrics_path}")
    print("=" * 60)
    print("HOAN TAT HUAN LUYEN MO HINH THANH CONG!")
    print("=" * 60)


if __name__ == "__main__":
    train()
