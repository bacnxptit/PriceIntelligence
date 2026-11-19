import os
import sys
from typing import Any

import pandas as pd
import psycopg
from dotenv import load_dotenv

# Load environment variables
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

POSTGRES_URL = (
    os.getenv("SUPABASE_DB_URL")
    or os.getenv("POSTGRES_URL")
    or os.getenv("DATABASE_URL")
)

SOURCE_TABLE = "clean_products"
ANALYTICS_TABLE = "iphone_price_analytics"


def classify_price_position(row: pd.Series) -> str:
    if pd.isna(row["price"]) or pd.isna(row["market_avg"]):
        return "Unknown"
    if row["price"] == row["market_min"] and row["price"] == row["market_max"]:
        return "Equal Price"
    elif row["price"] == row["market_min"]:
        return "Best Price (Cheapest)"
    elif row["price"] == row["market_max"]:
        return "Highest Price"
    elif row["price"] < row["market_avg"]:
        return "Below Average"
    else:
        return "Above Average"


def _db_val(col: str, v: Any) -> Any:
    if pd.isna(v) or v is None:
        return None
    if col in (
        "price", "listed_price", "capacity_gb", "market_min", "market_max",
        "market_avg", "market_median", "total_stores", "price_diff_vs_avg",
        "price_diff_vs_min"
    ):
        return int(v)
    if col in ("rating", "price_diff_pct"):
        return round(float(v), 2)
    if isinstance(v, pd.Timestamp):
        return v.to_pydatetime()
    return v


def run_price_feature_extraction():
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    print("=" * 80)
    print(f"BAT DAU TRICH CHON DAC TRUNG GIA LOI TU TABLE [{SOURCE_TABLE}]")
    print("=" * 80 + "\n")

    if not POSTGRES_URL:
        raise SystemExit("Thieu bien moi truong POSTGRES_URL / SUPABASE_DB_URL!")

    db_conn_url = POSTGRES_URL
    if db_conn_url.startswith("postgresql+psycopg://"):
        db_conn_url = "postgresql://" + db_conn_url.removeprefix("postgresql+psycopg://")

    # 1. DOC DU LIEU SACH TU POSTGRESQL
    print("1. Doc du lieu tu PostgreSQL...")
    with psycopg.connect(
        db_conn_url,
        prepare_threshold=None,
        sslmode=os.getenv("PGSSLMODE", "require"),
    ) as conn:
        with conn.cursor() as cur:
            cur.execute(f"SELECT * FROM {SOURCE_TABLE};")
            colnames = [desc[0] for desc in cur.description]
            records = cur.fetchall()

    df = pd.DataFrame(records, columns=colnames)
    print(f"   Da doc {len(df):,} ban ghi tu bang {SOURCE_TABLE}.")

    if df.empty:
        print("Bang du lieu rong! Hay chay truoc script bai3_etl_features_postgres.py.")
        return

    # 2. DAC TRUNG LOI 1: MARKET PRICE
    print("\n2. Tinh toan Market Price theo tung dong san pham (product_match_key) & ngay crawl...")
    market_stats = (
        df.groupby(["product_match_key", "crawl_date"])
        .agg(
            market_min=("price", "min"),
            market_max=("price", "max"),
            market_avg=("price", "mean"),
            market_median=("price", "median"),
            total_stores=("store", "nunique"),
        )
        .reset_index()
    )

    market_stats["market_avg"] = market_stats["market_avg"].round(0)

    # Merge chi so thi truong quay tro lai dataframe
    df_analytics = df.merge(
        market_stats,
        on=["product_match_key", "crawl_date"],
        how="left",
    )

    # 3. DAC TRUNG LOI 2: PRICE DIFFERENCE
    print("3. Tinh do lech gia (Price Difference & Percentage)...")
    df_analytics["price_diff_vs_avg"] = (
        df_analytics["price"] - df_analytics["market_avg"]
    )
    df_analytics["price_diff_vs_min"] = (
        df_analytics["price"] - df_analytics["market_min"]
    )
    df_analytics["price_diff_pct"] = (
        (df_analytics["price_diff_vs_avg"] / df_analytics["market_avg"]) * 100
    ).round(2)

    # 4. DAC TRUNG LOI 3: PRICE POSITION
    print("4. Phan loai vi tri gia (Price Position)...")
    df_analytics["price_position"] = df_analytics.apply(
        classify_price_position, axis=1
    )

    # 5. LUU BANG DAC TRUNG GIA VAO POSTGRESQL
    print(f"\n5. Ghi du lieu vao bang [{ANALYTICS_TABLE}] tren PostgreSQL...")

    recreate_table_query = f"""
    DROP TABLE IF EXISTS {ANALYTICS_TABLE};
    CREATE TABLE {ANALYTICS_TABLE} (
        id SERIAL PRIMARY KEY,
        title TEXT,
        "ID" TEXT,
        brand VARCHAR(50),
        model VARCHAR(100),
        capacity_gb INT,
        product_match_key VARCHAR(150),
        store VARCHAR(100),
        price BIGINT,
        listed_price BIGINT,
        market_min BIGINT,
        market_max BIGINT,
        market_avg BIGINT,
        market_median BIGINT,
        total_stores INT,
        price_diff_vs_avg BIGINT,
        price_diff_vs_min BIGINT,
        price_diff_pct FLOAT,
        price_position VARCHAR(50),
        crawled_at TIMESTAMPTZ,
        crawl_date DATE,
        url TEXT
    );
    """

    target_cols = [
        "title", "ID", "brand", "model", "capacity_gb",
        "product_match_key", "store", "price", "listed_price",
        "market_min", "market_max", "market_avg", "market_median",
        "total_stores", "price_diff_vs_avg", "price_diff_vs_min",
        "price_diff_pct", "price_position", "crawled_at",
        "crawl_date", "url",
    ]

    insert_sql = f"""
    INSERT INTO {ANALYTICS_TABLE} (
        {", ".join(['"' + c + '"' if c == "ID" else c for c in target_cols])}
    ) VALUES ({", ".join(["%s"] * len(target_cols))});
    """

    rows = []
    for r in df_analytics.itertuples(index=False):
        row_vals = tuple(_db_val(c, getattr(r, c)) for c in target_cols)
        rows.append(row_vals)

    with psycopg.connect(
        db_conn_url,
        prepare_threshold=None,
        sslmode=os.getenv("PGSSLMODE", "require"),
    ) as conn:
        with conn.cursor() as cur:
            cur.execute(recreate_table_query)
            if rows:
                cur.executemany(insert_sql, rows)
            conn.commit()

            cur.execute(f"SELECT COUNT(*) FROM {ANALYTICS_TABLE};")
            loaded_count = cur.fetchone()[0]

            display_cols = [
                "product_match_key", "store", "price", "market_min",
                "market_avg", "price_diff_vs_avg", "price_position",
            ]
            cur.execute(f"""
            SELECT {", ".join(display_cols)}
            FROM {ANALYTICS_TABLE}
            ORDER BY product_match_key, price ASC
            LIMIT 10;
            """)
            sample_rows = cur.fetchall()

    print(f"[LOAD] Da tinh toan va luu {loaded_count:,} ban ghi vao bang {ANALYTICS_TABLE} thanh cong!\n")

    # 6. IN KET QUA KIEM TRA MAU
    print("[VERIFY] 10 ban ghi mau trich chon dac trung gia loi:")
    print("=" * 115)
    sample_df = pd.DataFrame(sample_rows, columns=display_cols)
    print(sample_df.to_string(index=False))
    print("=" * 115)


if __name__ == "__main__":
    run_price_feature_extraction()
