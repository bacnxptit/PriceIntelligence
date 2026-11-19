import os
import re
import sys
import matplotlib
# Use Agg backend for non-interactive / headless environment
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import psycopg
import seaborn as sns
from dotenv import load_dotenv

# Load environment variables
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

POSTGRES_URL = (
    os.getenv("SUPABASE_DB_URL")
    or os.getenv("POSTGRES_URL")
    or os.getenv("DATABASE_URL")
)

SOURCE_TABLE = "clean_products"


def detect_outliers(target_key: str = None) -> str | None:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    if not POSTGRES_URL:
        raise SystemExit("Thieu bien moi truong POSTGRES_URL / SUPABASE_DB_URL!")

    db_conn_url = POSTGRES_URL
    if db_conn_url.startswith("postgresql+psycopg://"):
        db_conn_url = "postgresql://" + db_conn_url.removeprefix("postgresql+psycopg://")

    # 1. DOC DU LIEU TU POSTGRESQL
    print("1. Doc du lieu tu PostgreSQL...")
    with psycopg.connect(
        db_conn_url,
        prepare_threshold=None,
        sslmode=os.getenv("PGSSLMODE", "require"),
    ) as conn:
        with conn.cursor() as cur:
            cur.execute(f"""
            SELECT title, "ID", brand, model, capacity_gb, product_match_key, store, price
            FROM {SOURCE_TABLE};
            """)
            colnames = [desc[0] for desc in cur.description]
            records = cur.fetchall()

    df = pd.DataFrame(records, columns=colnames)

    if df.empty:
        print("Bang du lieu rong!")
        return None

    # Chon san pham muc tieu
    available_keys = df["product_match_key"].value_counts()
    if target_key and target_key in available_keys:
        chosen_key = target_key
    else:
        # Mac dinh chon key pho bien nhat
        chosen_key = available_keys.index[0]

    df_target = df[df["product_match_key"] == chosen_key].copy()
    print(f"\n>> Dang phan tich Outliers cho san pham: [{chosen_key}] ({len(df_target)} ban ghi)")

    # 2. TINH TOAN CAC CHI SO THONG KE (IQR & Z-SCORE)
    prices = df_target["price"].astype(float)
    mean_price = prices.mean()
    std_price = prices.std() if len(prices) > 1 else 0.0

    q1 = prices.quantile(0.25)
    q3 = prices.quantile(0.75)
    iqr = q3 - q1
    lower_bound = max(0, q1 - 1.5 * iqr)
    upper_bound = q3 + 1.5 * iqr

    df_target["z_score"] = (
        (prices - mean_price) / std_price if std_price > 0 else 0.0
    ).round(4)
    df_target["is_iqr_outlier"] = (prices < lower_bound) | (prices > upper_bound)
    df_target["is_zscore_outlier"] = df_target["z_score"].abs() > 2.0

    outliers = df_target[df_target["is_iqr_outlier"] | df_target["is_zscore_outlier"]]

    # 3. IN BAO CAO CHI TIET
    print("=" * 80)
    print(f"BAO CAO THONG KE NGOAI LE (OUTLIERS) CHO SAN PHAM: [{chosen_key.upper()}]")
    print("=" * 80 + "\n")

    print(f"- Tong so mau thu thap duoc : {len(df_target)} ban ghi")
    print(f"- Gia trung binh (Mean)     : {mean_price:,.0f} d")
    print(f"- Do lech chuan (Std)       : {std_price:,.0f} d")
    print(f"- Khoang Tu phan vi (Q1-Q3) : {q1:,.0f} d --> {q3:,.0f} d (IQR = {iqr:,.0f} d)")
    print(f"- Nguong gia hop le (IQR)   : Tu {lower_bound:,.0f} d DEN {upper_bound:,.0f} d\n")

    print(f"Phat hien: {len(outliers)} diem gia ngoai le!")
    if not outliers.empty:
        print("\nDANH SACH DIEM NGOAI LE (OUTLIERS):")
        print("-" * 90)
        display_cols = ["title", "store", "price", "z_score", "is_iqr_outlier", "is_zscore_outlier"]
        print(outliers[display_cols].to_string(index=False))
        print("-" * 90)
    else:
        print(f"Tat ca cac muc gia cua [{chosen_key}] deu nam trong nguong an toan!")

    # 4. VE BIEU DO HINH ANH PREVIEW (BOXPLOT + STRIPPLOT)
    plt.figure(figsize=(10, 5))
    sns.set_theme(style="whitegrid")

    # Ve Boxplot
    sns.boxplot(
        x=df_target["price"],
        color="skyblue",
        width=0.4,
        fliersize=0,
    )

    # Ve cac diem du lieu thuc te de len (Stripplot)
    sns.stripplot(
        x=df_target["price"],
        color="darkblue",
        size=8,
        jitter=0.2,
        alpha=0.7,
    )

    # Danh dau duong nguong IQR
    plt.axvline(
        lower_bound,
        color="red",
        linestyle="--",
        label=f"Lower Bound: {lower_bound:,.0f}d",
    )
    plt.axvline(
        upper_bound,
        color="red",
        linestyle="--",
        label=f"Upper Bound: {upper_bound:,.0f}d",
    )

    plt.title(
        f"PHAN BO GIA VA DIEM NGOAI LE (BOXPLOT & STRIPPLOT)\nSan pham: {chosen_key.upper()}",
        fontsize=13,
        fontweight="bold",
    )
    plt.xlabel("Gia ban (VND)", fontsize=11)
    ax = plt.gca()
    ax.xaxis.set_major_formatter("{x:,.0f} d")
    plt.legend(loc="upper right")
    plt.tight_layout()

    # Luu hinh anh ra file
    output_img_path = os.path.join(os.path.dirname(__file__), f"outliers_boxplot_{chosen_key}.png")
    plt.savefig(output_img_path, dpi=300, bbox_inches="tight")
    plt.close()

    print(f"\nDa luu thanh cong bieu do Boxplot vao: {output_img_path}")
    return output_img_path


def main() -> None:
    target_key = sys.argv[1] if len(sys.argv) > 1 else None
    detect_outliers(target_key)


if __name__ == "__main__":
    main()
