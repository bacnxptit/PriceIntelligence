import os
import re
import sys
import urllib.parse
from datetime import datetime, timezone
from typing import Any

import pandas as pd
import psycopg
from dotenv import load_dotenv
from pymongo import MongoClient

# Load environment variables
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

MONGO_URI = os.getenv("MONGODB_URI") or os.getenv("MONGO_URI")
MONGO_DB_NAME = os.getenv("MONGODB_DB") or os.getenv("MONGO_DB") or "imdb"
POSTGRES_URL = (
    os.getenv("SUPABASE_DB_URL")
    or os.getenv("POSTGRES_URL")
    or os.getenv("DATABASE_URL")
)

# =============================================================
# HELPER FUNCTIONS CHUAN HOA & TRICH CHON DAC TRUNG
# =============================================================

def clean_price(val: Any) -> int | None:
    if pd.isna(val) or val is None:
        return None
    val_str = str(val).strip()
    digits = re.sub(r"[^\d]", "", val_str)
    if not digits:
        return None
    price = int(digits)
    # Loai bo gia bat thuong/ngoai le (< 500k hoac > 200tr)
    if price < 500_000 or price > 200_000_000:
        return None
    return price


def clean_reviews(val: Any) -> int:
    if pd.isna(val) or val is None:
        return 0
    digits = re.sub(r"[^\d]", "", str(val))
    return int(digits) if digits else 0


def clean_rating(val: Any) -> float | None:
    if pd.isna(val) or val is None:
        return None
    val_str = str(val).strip()
    if "chua co" in val_str.lower():
        return None
    match = re.search(r"(\d+(?:[.,]\d+)?)", val_str)
    if match:
        try:
            score = float(match.group(1).replace(",", "."))
            return score if 0 <= score <= 5 else None
        except ValueError:
            return None
    return None


def clean_model_name(title_or_cat: str) -> str:
    text = str(title_or_cat or "").replace("\xa0", " ").strip().lower()
    # Loai bo cac cum phu nhu (chinh hang vn/a)
    text = re.sub(r"\(.*?\)", " ", text)
    text = text.replace("-", " ").replace("|", " ")
    match = re.search(r"(?:iphone\s+)?([\w\s]+?)(?=\s+\d+(?:gb|tb)|$)", text)
    if match:
        model = match.group(1).strip()
    else:
        model = text
    model = re.sub(r"\biphone\b", "", model).strip()
    model = re.sub(r"\s+", " ", model).strip()
    return model if model else "unknown"


def clean_capacity_gb(val_str: Any) -> int | None:
    if pd.isna(val_str) or not val_str:
        return None
    val_str = str(val_str).upper().strip()
    match = re.search(r"(\d+)\s*(GB|TB)", val_str)
    if match:
        num, unit = int(match.group(1)), match.group(2)
        return int(num * 1024 if unit == "TB" else num)
    return None


STORE_MAP = {
    "apple.com": "Apple Store",
    "fptshop.com.vn": "FPT Shop",
    "thegioididong.com": "TGDD",
    "topzone.vn": "TopZone",
    "cellphones.com.vn": "CellphoneS",
    "viettelstore.vn": "Viettel Store",
    "hoanghamobile.com": "Hoang Ha Mobile",
    "mobilecity.vn": "Mobile City",
}


def detect_store(url_str: Any) -> str:
    if not url_str or pd.isna(url_str):
        return "Unknown"
    domain = urllib.parse.urlparse(str(url_str)).netloc.lower().replace("www.", "")
    for key, store_name in STORE_MAP.items():
        if key in domain:
            return store_name
    return domain if domain else "Unknown"


# =============================================================
# PARSER CHUYEN BIET CHO TUNG COLLECTION
# =============================================================

def transform_generic_doc(doc: dict, default_store_name: str = "Unknown") -> dict:
    title = doc.get("product_title") or doc.get("title") or doc.get("name") or ""
    cat = doc.get("category") or doc.get("product_series") or title
    model = clean_model_name(title if title else cat)

    cap_gb = clean_capacity_gb(doc.get("capacity")) or clean_capacity_gb(title)
    sku = (
        doc.get("part_number")
        or doc.get("sku")
        or doc.get("product_code")
        or doc.get("product_id")
        or doc.get("url")
        or doc.get("link")
        or str(doc.get("_id"))
    )

    raw_price = (
        doc.get("price")
        or doc.get("current_price")
        or doc.get("price_sale")
        or doc.get("price_raw")
        or doc.get("price_string")
    )
    raw_listed_price = (
        doc.get("original_price")
        or doc.get("price_original")
        or doc.get("price_old")
    )

    raw_rating = (
        doc.get("rating_score")
        or doc.get("average_rating")
        or doc.get("rating")
    )
    raw_reviews = (
        doc.get("review_count")
        or doc.get("total_rated")
        or doc.get("reviews")
    )

    url = doc.get("url") or doc.get("product_url") or doc.get("link") or ""

    crawled_at = doc.get("crawled_at")
    if isinstance(crawled_at, dict) and "$date" in crawled_at:
        crawled_at = crawled_at["$date"]
    elif not crawled_at and "_id" in doc and hasattr(doc["_id"], "generation_time"):
        crawled_at = doc["_id"].generation_time

    return {
        "title": title,
        "ID": str(sku),
        "brand": "apple",
        "model": model,
        "capacity_gb": cap_gb,
        "raw_price": raw_price,
        "raw_listed_price": raw_listed_price,
        "raw_rating": raw_rating,
        "raw_reviews": raw_reviews,
        "url": url,
        "crawled_at_raw": crawled_at,
    }


# =============================================================
# QUY TRINH ETL PIPELINE CHINH
# =============================================================

def run_etl_pipeline():
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    print("=" * 80)
    print("BAT DAU ETL PIPELINE TICH HOP DAC TRUNG NANG CAO (BAI 5)")
    print("(MONGO -> POSTGRESQL)")
    print("=" * 80)

    if not MONGO_URI:
        raise SystemExit("Thieu MONGODB_URI trong .env!")
    if not POSTGRES_URL:
        raise SystemExit("Thieu SUPABASE_DB_URL trong .env!")

    # Format postgres url for psycopg 3
    db_conn_url = POSTGRES_URL
    if db_conn_url.startswith("postgresql+psycopg://"):
        db_conn_url = "postgresql://" + db_conn_url.removeprefix("postgresql+psycopg://")

    # --- BUOC 1: EXTRACT ---
    print("\n# --- BUOC 1: EXTRACT ---")
    mongo_client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=10000)
    mongo_client.admin.command("ping")
    mongo_db = mongo_client[MONGO_DB_NAME]

    collections = sorted([c for c in mongo_db.list_collection_names() if c.startswith("iphone_")])
    if not collections:
        collections = [c for c in ["apple_store", "fptshop"] if c in mongo_db.list_collection_names()]

    raw_records = []
    for col_name in collections:
        docs = list(mongo_db[col_name].find({}))
        for d in docs:
            raw_records.append(transform_generic_doc(d))

    extract_count = len(raw_records)
    print(f"[EXTRACT] Tong cong doc va chuan hoa cau truc: {extract_count:,} ban ghi tho tu {len(collections)} collections.")

    if extract_count == 0:
        print("Khong co du lieu!")
        return

    df = pd.DataFrame(raw_records)

    # --- BUOC 2: TRANSFORM ---
    print("\n# --- BUOC 2: TRANSFORM ---")
    # 2.1 CLEAN: Loc bo ban ghi thieu Title hoac Gia
    df_clean = df.dropna(subset=["title", "raw_price"]).copy()
    clean_count = len(df_clean)
    print(f"[CLEAN] Con lai: {clean_count:,} ban ghi sau khi loc thieu Title/Gia.")

    # 2.2 NORMALIZE & FEATURE EXTRACTION
    df_clean["price"] = df_clean["raw_price"].apply(clean_price)
    df_clean["listed_price"] = df_clean["raw_listed_price"].apply(clean_price)

    df_clean = df_clean.dropna(subset=["price"]).copy()
    df_clean["price"] = df_clean["price"].astype("int64")

    df_clean["rating"] = df_clean["raw_rating"].apply(clean_rating)
    df_clean["reviews"] = df_clean["raw_reviews"].apply(clean_reviews).astype(int)
    df_clean["store"] = df_clean["url"].apply(detect_store)

    # Ep kieu capacity_gb sang Int64 (Nullable Integer) tranh .0
    df_clean["capacity_gb"] = df_clean["capacity_gb"].astype("Int64")

    # Tao Rule-based Match Key (brand_model_capacity)
    df_clean["product_match_key"] = (
        df_clean["brand"] + "_" + df_clean["model"] + "_" + df_clean["capacity_gb"].astype(str)
    ).str.replace(r"\s+", "", regex=True)

    # Chuan hoa mui gio Asia/Ho_Chi_Minh & Ngay Crawl
    df_clean["crawled_at"] = pd.to_datetime(df_clean["crawled_at_raw"], utc=True, errors="coerce")
    df_clean["crawled_at"] = df_clean["crawled_at"].dt.tz_convert("Asia/Ho_Chi_Minh")
    df_clean["crawl_date"] = df_clean["crawled_at"].dt.date

    normalize_count = len(df_clean)
    print(f"[NORMALIZE] Sau chuan hoa & tach Features: {normalize_count:,} ban ghi.")

    # 2.3 DEDUPLICATE: Loc trung theo (store, ID, crawl_date)
    df_sorted = df_clean.sort_values("crawled_at", ascending=False)
    df_dedup = df_sorted.drop_duplicates(subset=["store", "ID", "crawl_date"], keep="first").reset_index(drop=True)

    target_columns = [
        "title", "ID", "brand", "model", "capacity_gb",
        "product_match_key", "store", "price", "listed_price",
        "rating", "reviews", "crawled_at", "crawl_date", "url",
    ]
    df_final = df_dedup[target_columns].copy()
    dedup_count = len(df_final)
    print(f"[DEDUP] Con lai: {dedup_count:,} ban ghi sau khi loai trung lap.")

    # --- BUOC 3: LOAD (GHI VAO POSTGRESQL SUPABASE) ---
    print("\n# --- BUOC 3: LOAD (GHI VAO POSTGRESQL SUPABASE) ---")
    create_table_query = """
    DROP TABLE IF EXISTS clean_products;
    CREATE TABLE clean_products (
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
        rating FLOAT,
        reviews INT,
        crawled_at TIMESTAMPTZ,
        crawl_date DATE,
        url TEXT
    );
    """

    insert_sql = """
    INSERT INTO clean_products (
        title, "ID", brand, model, capacity_gb, product_match_key,
        store, price, listed_price, rating, reviews, crawled_at, crawl_date, url
    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
    """

    # Prepare tuples for psycopg insertion
    def _val(col, v):
        if pd.isna(v):
            return None
        if col in ("price", "listed_price", "capacity_gb", "reviews"):
            return int(v)
        if col == "rating":
            return round(float(v), 2)
        if isinstance(v, pd.Timestamp):
            return v.to_pydatetime()
        return v

    rows = []
    for r in df_final.itertuples(index=False):
        row_vals = tuple(_val(c, getattr(r, c)) for c in target_columns)
        rows.append(row_vals)

    with psycopg.connect(
        db_conn_url,
        connect_timeout=15,
        prepare_threshold=None,
        sslmode=os.getenv("PGSSLMODE", "require"),
    ) as conn:
        with conn.cursor() as cur:
            cur.execute(create_table_query)
            if rows:
                cur.executemany(insert_sql, rows)
            conn.commit()

            cur.execute("SELECT COUNT(*) FROM clean_products")
            load_count = cur.fetchone()[0]

            cur.execute("""
            SELECT title, brand, model, capacity_gb, product_match_key, store, price
            FROM clean_products LIMIT 5;
            """)
            sample_rows = cur.fetchall()

            cur.execute("""
            SELECT store, COUNT(*) as count
            FROM clean_products GROUP BY store ORDER BY count DESC;
            """)
            stats_rows = cur.fetchall()

    print(f"[LOAD] Ghi thanh cong {load_count:,} ban ghi da tach dac trung vao PostgreSQL!")

    # --- BUOC 4: VERIFY ---
    print("\n# --- BUOC 4: VERIFY (DOC KIEM TRA LAI DU LIEU) ---")
    print("Thong ke san pham thuc te theo Store trong PostgreSQL:")
    df_stats = pd.DataFrame(stats_rows, columns=["Store", "Count"])
    print(df_stats.to_string(index=False))

    print("\n5 ban ghi mau day du thuoc tinh chuan hoa:")
    print("=" * 115)
    sample_df = pd.DataFrame(
        sample_rows,
        columns=["title", "brand", "model", "capacity_gb", "product_match_key", "store", "price"],
    )
    print(sample_df.to_string(index=False))
    print("=" * 115)

    # --- BUOC 5: BAO CAO KET QUA ETL ---
    print("\n\n================ BAO CAO TIEN TRINH ETL PIPELINE HOAN CHINH ================")
    print(f"1. Extract (So ban ghi tu Mongo)            : {extract_count:,}")
    print(f"2. Clean (Sau khi loc thieu field)          : {clean_count:,}")
    print(f"3. Normalize (Sau chuan hoa & tach Features): {normalize_count:,}")
    print(f"4. Dedup (Sau khi loai trung)               : {dedup_count:,}")
    print(f"5. Load (Ghi vao Postgres Supabase)         : {load_count:,}")
    print("============================================================================")
    print("TICH HOP CHUAN HOA DAC TRUNG VAO POSTGRESQL THANH CONG!")


if __name__ == "__main__":
    run_etl_pipeline()
