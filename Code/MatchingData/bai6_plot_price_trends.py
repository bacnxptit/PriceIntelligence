import os
import sys
import matplotlib
# Use Agg backend for non-interactive / headless environment
matplotlib.use("Agg")
import matplotlib.pyplot as plt
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

ANALYTICS_TABLE = "iphone_price_analytics"


def plot_price_trends(target_match_key: str = None) -> str | None:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    if not POSTGRES_URL:
        raise SystemExit("Thieu bien moi truong POSTGRES_URL / SUPABASE_DB_URL!")

    db_conn_url = POSTGRES_URL
    if db_conn_url.startswith("postgresql+psycopg://"):
        db_conn_url = "postgresql://" + db_conn_url.removeprefix("postgresql+psycopg://")

    # 1. KIEM TRA VA CHON MATCH KEY CO SAN TRONG DATABASE
    with psycopg.connect(
        db_conn_url,
        prepare_threshold=None,
        sslmode=os.getenv("PGSSLMODE", "require"),
    ) as conn:
        with conn.cursor() as cur:
            cur.execute(f"""
            SELECT product_match_key, COUNT(DISTINCT store) as store_count, COUNT(*) as total_count
            FROM {ANALYTICS_TABLE}
            GROUP BY product_match_key
            ORDER BY store_count DESC, total_count DESC;
            """)
            keys_info = cur.fetchall()

    if not keys_info:
        print(f"\nKhong co du lieu trong bang [{ANALYTICS_TABLE}]. Hay chay truoc script bai5_price_analytics.py!")
        return None

    print("=" * 80)
    print("DANH SACH TOP 10 PRODUCT_MATCH_KEY PHO BIEN NHAT:")
    print("=" * 80)
    for idx, (k, s_cnt, t_cnt) in enumerate(keys_info[:10], 1):
        print(f" {idx:2d}. {k:<25} ({s_cnt} cua hang, {t_cnt} ban ghi)")

    # Chon key muc tieu
    if target_match_key and any(k[0] == target_match_key for k in keys_info):
        chosen_key = target_match_key
    else:
        # Uu tien chon san pham co nhieu store nhat de bieu do so sanh truc quan nhat
        chosen_key = keys_info[0][0]

    print(f"\n>> Dang chon ve bieu do cho san pham: [{chosen_key}]")

    # 2. TRUY VAN DU LIEU DE VE BIEU DO
    query = f"""
    SELECT product_match_key, store, price, market_avg, market_min, crawl_date
    FROM {ANALYTICS_TABLE}
    WHERE product_match_key = %s
    ORDER BY crawl_date ASC, price ASC;
    """
    with psycopg.connect(
        db_conn_url,
        prepare_threshold=None,
        sslmode=os.getenv("PGSSLMODE", "require"),
    ) as conn:
        with conn.cursor() as cur:
            cur.execute(query, (chosen_key,))
            colnames = [desc[0] for desc in cur.description]
            records = cur.fetchall()

    df_product = pd.DataFrame(records, columns=colnames)
    df_product["crawl_date"] = pd.to_datetime(df_product["crawl_date"])

    # 3. THIET LAP VA VE BIEU DO
    plt.figure(figsize=(12, 6))
    sns.set_theme(style="whitegrid")

    # Duong gia tung Store
    sns.lineplot(
        data=df_product,
        x="crawl_date",
        y="price",
        hue="store",
        marker="o",
        linewidth=2.5,
        markersize=8,
    )

    # Duong gia trung binh thi truong (net dut mau do)
    df_avg = (
        df_product.groupby("crawl_date")["market_avg"]
        .mean()
        .reset_index()
    )
    plt.plot(
        df_avg["crawl_date"],
        df_avg["market_avg"],
        label="Market Average (Trung binh thi truong)",
        color="red",
        linestyle="--",
        linewidth=2,
    )

    # Dinh dang bieu do
    plt.title(
        f"BIEU DO BIEN DONG GIA THEO THOI GIAN\nSan pham: {chosen_key.upper()}",
        fontsize=14,
        fontweight="bold",
    )
    plt.xlabel("Ngay Crawl Du Lieu (Crawl Date)", fontsize=11)
    plt.ylabel("Gia Ban (VND)", fontsize=11)

    # Dinh dang so tien VND o truc Y
    ax = plt.gca()
    ax.yaxis.set_major_formatter("{x:,.0f} d")

    plt.xticks(rotation=45)
    plt.legend(
        title="Nguon Du Lieu",
        bbox_to_anchor=(1.05, 1),
        loc="upper left",
    )
    plt.tight_layout()

    # Luu hinh anh ra file
    output_img_path = os.path.join(os.path.dirname(__file__), f"price_trend_{chosen_key}.png")
    plt.savefig(output_img_path, dpi=300, bbox_inches="tight")
    plt.close()

    print(f"\nDa luu thanh cong bieu do bien dong gia vao: {output_img_path}")
    return output_img_path


def main() -> None:
    target_key = sys.argv[1] if len(sys.argv) > 1 else None
    plot_price_trends(target_key)


if __name__ == "__main__":
    main()
