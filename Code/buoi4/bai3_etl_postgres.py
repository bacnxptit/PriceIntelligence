import os
import sys
from typing import Any

import pandas as pd
import psycopg
from dotenv import load_dotenv
from pymongo import MongoClient

from Bai1_normalize import (
    MONGO_COLLECTION,
    MONGO_DB,
    fetch_raw_documents,
    normalize,
    parse_price,
    prepare_for_normalize,
)
from Bai2_duplicate import deduplicate


load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

TABLE_NAME = "clean_products"
OUTPUT_COLUMNS = [
    "title",
    "ID",
    "store",
    "price",
    "listed_price",
    "capacity_gb",
    "rating",
    "reviews",
    "crawled_at",
    "crawl_date",
    "url",
]

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS clean_products (
    title TEXT NOT NULL,
    "ID" TEXT PRIMARY KEY,
    store TEXT,
    price BIGINT,
    listed_price BIGINT,
    capacity_gb INTEGER,
    rating NUMERIC(3, 2),
    reviews INTEGER NOT NULL,
    crawled_at TIMESTAMPTZ,
    crawl_date DATE,
    url TEXT
)
"""

UPSERT_SQL = """
INSERT INTO clean_products (
    title, "ID", store, price, listed_price, capacity_gb, rating,
    reviews, crawled_at, crawl_date, url
) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
ON CONFLICT ("ID") DO UPDATE SET
    title = EXCLUDED.title,
    store = EXCLUDED.store,
    price = EXCLUDED.price,
    listed_price = EXCLUDED.listed_price,
    capacity_gb = EXCLUDED.capacity_gb,
    rating = EXCLUDED.rating,
    reviews = EXCLUDED.reviews,
    crawled_at = EXCLUDED.crawled_at,
    crawl_date = EXCLUDED.crawl_date,
    url = EXCLUDED.url
"""

SELECT_SAMPLE_SQL = """
SELECT title, "ID", store, price, listed_price, capacity_gb, rating,
       reviews, crawled_at, crawl_date, url
FROM clean_products
ORDER BY store, title, "ID"
LIMIT 5
"""


def clean_documents(documents: list[dict[str, Any]]) -> pd.DataFrame:
    """Remove documents without title, SKU, or a valid price (0 < price < 200,000,000)."""
    source = prepare_for_normalize(documents)
    valid_title = source["title"].astype("string").str.strip().ne("").fillna(False)
    valid_sku = source["sku"].astype("string").str.strip().ne("").fillna(False)

    parsed_prices = source["current_price"].apply(parse_price)
    valid_price = parsed_prices.notna() & (parsed_prices > 0) & (parsed_prices < 200_000_000)

    return source.loc[valid_title & valid_sku & valid_price].copy()


def _database_value(column_name: str, value: Any) -> Any:
    """Convert pandas/numpy values to standard Python/PostgreSQL compatible types."""
    if pd.isna(value):
        return None
    if column_name in ("price", "listed_price", "capacity_gb", "reviews"):
        return int(value)
    if column_name == "rating":
        return round(float(value), 2)
    if isinstance(value, pd.Timestamp):
        return value.to_pydatetime()
    return value


def _rows_for_load(df: pd.DataFrame) -> list[tuple[Any, ...]]:
    """Prepare typed tuples for psycopg execute."""
    rows: list[tuple[Any, ...]] = []
    for row in df[OUTPUT_COLUMNS].itertuples(index=False):
        row_values = tuple(
            _database_value(col, getattr(row, col)) for col in OUTPUT_COLUMNS
        )
        rows.append(row_values)
    return rows


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    mongo_uri = os.getenv("MONGODB_URI")
    if not mongo_uri:
        raise SystemExit("Thieu bien moi truong MONGODB_URI.")

    postgres_url = (
        os.getenv("SUPABASE_DB_URL")
        or os.getenv("POSTGRES_URL")
        or os.getenv("DATABASE_URL")
    )
    if not postgres_url:
        raise SystemExit(
            "Thieu SUPABASE_DB_URL (hoac POSTGRES_URL/DATABASE_URL) cho PostgreSQL."
        )

    # Normalize dialect prefix for psycopg 3
    if postgres_url.startswith("postgresql+psycopg://"):
        postgres_url = "postgresql://" + postgres_url.removeprefix(
            "postgresql+psycopg://"
        )

    # 1. EXTRACT
    print("--- 1. EXTRACT ---")
    with MongoClient(mongo_uri, serverSelectionTimeoutMS=10000) as client:
        client.admin.command("ping")
        documents = fetch_raw_documents(client, MONGO_DB, MONGO_COLLECTION)

    extracted_count = len(documents)
    print(f"Trich xuat: {extracted_count} documents tu MongoDB ({MONGO_DB})")

    # 2. CLEAN
    print("\n--- 2. CLEAN ---")
    cleaned_df = clean_documents(documents)
    clean_count = len(cleaned_df)
    print(f"Lam sach: {clean_count} documents hop le (loai bo {extracted_count - clean_count} thieu title/sku/gia)")

    # 3. NORMALIZE
    print("\n--- 3. NORMALIZE ---")
    normalized_df = normalize(cleaned_df)
    normalized_count = len(normalized_df)
    print(f"Chuan hoa: {normalized_count} documents")

    # 4. DEDUPLICATE
    print("\n--- 4. DEDUPLICATE ---")
    deduplicated_df = deduplicate(normalized_df)
    # Ensure ID uniqueness as well
    deduplicated_df = deduplicated_df.drop_duplicates(subset=["_id"]).reset_index(drop=True)
    dedup_count = len(deduplicated_df)
    print(f"Khu trung lap: {dedup_count} documents duy nhat (giam {normalized_count - dedup_count})")

    # Prepare DataFrame for Database Load
    load_df = deduplicated_df.rename(columns={"_id": "ID"})[OUTPUT_COLUMNS].copy()
    rows = _rows_for_load(load_df)

    # Also save local backups
    local_csv_path = os.path.join(os.path.dirname(__file__), "clean_products.csv")
    load_df.to_csv(local_csv_path, index=False, encoding="utf-8-sig")
    print(f"\nDa luu backup du lieu sach vao file CSV: {local_csv_path}")

    # 5. LOAD TO POSTGRESQL
    print("\n--- 5. LOAD TO POSTGRESQL ---")
    print(f"Ket noi den PostgreSQL...")
    try:
        # Note: prepare_threshold=None is required for transaction poolers like Supabase PgBouncer (port 6543)
        with psycopg.connect(
            postgres_url,
            connect_timeout=15,
            prepare_threshold=None,
            sslmode=os.getenv("PGSSLMODE", "require"),
        ) as connection:
            with connection.cursor() as cursor:
                cursor.execute(CREATE_TABLE_SQL)
                # Full refresh: delete old rows and batch insert clean records
                cursor.execute("DELETE FROM clean_products")
                if rows:
                    cursor.executemany(UPSERT_SQL, rows)

                cursor.execute("SELECT COUNT(*) FROM clean_products")
                loaded_count = cursor.fetchone()[0]

                cursor.execute(SELECT_SAMPLE_SQL)
                sample_rows = cursor.fetchall()

        print(f"Nap vao PostgreSQL thanh cong! So ban ghi: {loaded_count}")

    except Exception as e:
        print(f"\n[CANH BAO] Khong the nap vao PostgreSQL qua mang: {e}")
        print("Luu tru fallback: Luu vao SQLite local tai clean_products.db...")
        import sqlite3
        sqlite_path = os.path.join(os.path.dirname(__file__), "clean_products.db")
        with sqlite3.connect(sqlite_path) as conn:
            load_df.to_sql("clean_products", conn, if_exists="replace", index=False)
        print(f"Da luu thanh cong vao SQLite: {sqlite_path}")
        loaded_count = len(load_df)
        sample_rows = []

    # BAO CAO TONG KET
    print("\n================ BAO CAO ETL PIPELINE ================")
    print(f"MongoDB Target:    {MONGO_DB} | Collection(s): {MONGO_COLLECTION}")
    print(f"PostgreSQL Table:  {TABLE_NAME}")
    print(f"1. Extract:        {extracted_count} ban ghi raw")
    print(f"2. Clean:          {clean_count} ban ghi hop le")
    print(f"3. Normalize:      {normalized_count} ban ghi")
    print(f"4. Deduplicate:    {dedup_count} ban ghi duy nhat")
    print(f"5. Load:           {len(rows)} ban ghi duoc nap")
    print(f"6. Verify in DB:   {loaded_count} ban ghi hien huu")
    print("======================================================")

    if sample_rows:
        print("\n5 ban ghi mau doc lai tu PostgreSQL:")
        sample_df = pd.DataFrame(sample_rows, columns=OUTPUT_COLUMNS)
        print(sample_df.to_string(index=False))


if __name__ == "__main__":
    main()
