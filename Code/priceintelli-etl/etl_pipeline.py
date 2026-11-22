import os
import re
import sys
from datetime import datetime, timedelta, timezone
from urllib.parse import urlparse
from typing import Any

import pandas as pd
import psycopg
from dotenv import load_dotenv
from pymongo import MongoClient

# ============================================================
# CAU HINH
# ============================================================
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

MONGO_URI = (
    os.getenv("MONGODB_URI")
    or os.getenv("MONGO_URI")
    or os.getenv("DATABASE_URL_MONGO")
)
MONGO_DB = os.getenv("MONGODB_DB") or os.getenv("MONGO_DB") or "imdb"
MONGO_COLLECTION = os.getenv("MONGO_COLLECTION", "all")

PG_URL = (
    os.getenv("SUPABASE_DB_URL")
    or os.getenv("POSTGRES_URL")
    or os.getenv("DATABASE_URL")
)

STORE_DOMAIN_MAP = {
    "fptshop.com.vn": "FPT Shop",
    "thegioididong.com": "The Gioi Di Dong",
    "topzone.vn": "TopZone",
    "cellphones.com.vn": "CellphoneS",
    "hoanghamobile.com": "Hoang Ha Mobile",
    "viettelstore.vn": "Viettel Store",
    "mobilecity.vn": "Mobile City",
    "apple.com": "Apple Vietnam",
}

def get_pg_connection_url() -> str:
    if not PG_URL:
        raise ValueError("Thieu bien moi truong SUPABASE_DB_URL / POSTGRES_URL!")
    url = PG_URL
    if url.startswith("postgresql+psycopg://"):
        url = "postgresql://" + url.removeprefix("postgresql+psycopg://")
    return url


# ============================================================
# EXTRACT
# ============================================================
def extract(since_hours: int = None) -> pd.DataFrame:
    if not MONGO_URI:
        raise ValueError(
            "Khong tim thay cau hinh MONGODB_URI hoac MONGO_URI! "
            "Vui long kiem tra GitHub Secrets hoac file .env."
        )

    masked_uri = re.sub(r":([^@]+)@", ":****@", MONGO_URI)
    print(f"[Extract] Dang ket noi toi MongoDB: {masked_uri} (Database: {MONGO_DB})")

    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=15000)
    db = client[MONGO_DB]

    if MONGO_COLLECTION and MONGO_COLLECTION not in ("all", "*", "iphone_*"):
        collections = [MONGO_COLLECTION]
    else:
        collections = sorted([c for c in db.list_collection_names() if c.startswith("iphone_")])
        if not collections:
            collections = ["raw_prices"]

    all_records = []
    since = datetime.now(timezone.utc) - timedelta(hours=since_hours) if since_hours else None

    for col in collections:
        query = {"crawled_at": {"$gte": since}} if since else {}
        cursor = db[col].find(query)
        docs = list(cursor)

        # Fallback neu loc theo gio khong co ban ghi nao (lay toan bo collection)
        if not docs and since:
            docs = list(db[col].find({}))

        for d in docs:
            title = d.get("product_title") or d.get("title") or d.get("name") or ""
            sku = (
                d.get("sku")
                or d.get("part_number")
                or d.get("product_code")
                or d.get("product_id")
                or d.get("url")
                or d.get("link")
                or str(d.get("_id"))
            )
            current_price = (
                d.get("current_price")
                or d.get("price")
                or d.get("price_sale")
                or d.get("price_raw")
                or d.get("price_string")
            )
            original_price = (
                d.get("original_price")
                or d.get("price_original")
                or d.get("price_old")
            )
            url = d.get("url") or d.get("product_url") or d.get("link") or ""
            capacity = d.get("capacity") or d.get("storage")

            crawled_at = d.get("crawled_at")
            if not crawled_at and "_id" in d and hasattr(d["_id"], "generation_time"):
                crawled_at = d["_id"].generation_time
            if not crawled_at:
                crawled_at = datetime.now(timezone.utc)

            all_records.append({
                "title": str(title).strip(),
                "sku": str(sku).strip(),
                "current_price": current_price,
                "original_price": original_price,
                "capacity": capacity,
                "crawled_at": crawled_at,
                "url": url,
            })

    client.close()
    df = pd.DataFrame(all_records)
    print(f"[Extract] {len(df)} ban ghi tu MongoDB")
    return df


# ============================================================
# CLEAN
# ============================================================
def clean(df: pd.DataFrame) -> pd.DataFrame:
    if len(df) == 0:
        return df
    initial = len(df)
    df = df.dropna(subset=["title", "sku", "current_price"]).copy()
    df = df[df["title"].astype(str).str.strip() != ""]
    df = df[df["sku"].astype(str).str.strip() != ""]
    df = df[df["current_price"].notna()]
    print(f"[Clean] {initial} -> {len(df)}")
    return df


# ============================================================
# NORMALIZE
# ============================================================
def parse_price(x: Any) -> int | None:
    if pd.isna(x) or x is None:
        return None
    cleaned = re.sub(r"[^\d]", "", str(x))
    if not cleaned:
        return None
    p = int(cleaned)
    return round(p / 10000) * 10000 if 0 < p < 200_000_000 else None


def parse_capacity(x: Any) -> int | None:
    if pd.isna(x) or not x:
        return None
    s = str(x).upper().replace(" ", "")
    m = re.search(r"(\d+)(GB|TB)", s)
    if not m:
        return None
    v, u = int(m.group(1)), m.group(2)
    return v * 1024 if u == "TB" else v


def get_store(url: Any) -> str | None:
    if pd.isna(url) or not url:
        return None
    d = urlparse(str(url)).netloc.lower().replace("www.", "")
    for k, v in STORE_DOMAIN_MAP.items():
        if k in d:
            return v
    return None


def normalize(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["store"] = df["url"].apply(get_store)
    df["price"] = df["current_price"].apply(parse_price)
    df["listed_price"] = df["original_price"].apply(parse_price)

    # Parse dung luong tu capacity, fallback tu title
    cap_col = df["capacity"].apply(parse_capacity) if "capacity" in df else pd.Series([None] * len(df))
    cap_title = df["title"].apply(parse_capacity)
    df["capacity_gb"] = cap_col.combine_first(cap_title)

    df["crawled_at"] = pd.to_datetime(df["crawled_at"], utc=True)
    df["crawled_at"] = df["crawled_at"].dt.tz_convert("Asia/Ho_Chi_Minh")
    df["crawl_date"] = df["crawled_at"].dt.date

    df["product_name"] = df.apply(
        lambda r: f"{str(r['title']).strip()} {int(r['capacity_gb'])}GB"
        if (pd.notna(r.get("capacity_gb")) and f"{int(r['capacity_gb'])}GB".lower() not in str(r['title']).lower().replace(" ", ""))
        else str(r["title"]).strip(),
        axis=1,
    )
    return df


# ============================================================
# VALIDATE
# ============================================================
def validate(df: pd.DataFrame) -> list[str]:
    errors = []
    if len(df) == 0:
        errors.append("Khong co du lieu moi")
    if df["price"].isna().sum() > len(df) * 0.5:
        errors.append(f"{df['price'].isna().sum()} ban ghi khong parse duoc gia")
    if df["store"].isna().sum() > 0:
        errors.append(f"{df['store'].isna().sum()} ban ghi khong nhan dien duoc san")
    return errors


# ============================================================
# LOG RUN
# ============================================================
def log_run(status: str, records: int, error: str = None, run_start: datetime = None) -> None:
    if run_start is None:
        run_start = datetime.now(timezone.utc)
    db_url = get_pg_connection_url()

    sql = """
    INSERT INTO pipeline_runs (
        job_name, started_at, finished_at, status, records_processed, error_message
    ) VALUES (%s, %s, %s, %s, %s, %s);
    """
    try:
        with psycopg.connect(db_url, prepare_threshold=None, sslmode=os.getenv("PGSSLMODE", "require")) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    sql,
                    ("etl_pipeline", run_start, datetime.now(timezone.utc), status, records, error)
                )
            conn.commit()
    except Exception as e:
        print(f"[Warning] Khong the ghi log pipeline: {e}")


# ============================================================
# LOAD (UPSERT - chong duplicate)
# ============================================================
def load(df: pd.DataFrame) -> tuple[int, int]:
    if len(df) == 0:
        print("[Load] Khong co du lieu")
        return 0, 0

    db_url = get_pg_connection_url()
    inserted, updated = 0, 0

    with psycopg.connect(db_url, prepare_threshold=None, sslmode=os.getenv("PGSSLMODE", "require")) as conn:
        with conn.cursor() as cur:
            # 1. Tu dong bo sung cac store chua ton tai vao dim_stores
            unique_stores = df["store"].dropna().unique().tolist()
            for s in unique_stores:
                cur.execute(
                    "INSERT INTO dim_stores (store_name) VALUES (%s) ON CONFLICT (store_name) DO NOTHING;",
                    (s,)
                )

            # 2. Tu dong bo sung cac product_name chua ton tai vao dim_products
            unique_products = df["product_name"].dropna().unique().tolist()
            for p in unique_products:
                cur.execute(
                    "INSERT INTO dim_products (product_name) VALUES (%s) ON CONFLICT (product_name) DO NOTHING;",
                    (p,)
                )
            conn.commit()

            # 3. Doc lai Map IDs
            cur.execute("SELECT product_id, product_name FROM dim_products;")
            products_map = {row[1]: row[0] for row in cur.fetchall()}

            cur.execute("SELECT store_id, store_name FROM dim_stores;")
            stores_map = {row[1]: row[0] for row in cur.fetchall()}

            df_load = df.copy()
            df_load["product_id"] = df_load["product_name"].map(products_map)
            df_load["store_id"] = df_load["store"].map(stores_map)
            df_load = df_load.dropna(subset=["product_id", "store_id", "price"])

            upsert_sql = """
            INSERT INTO fact_price_snapshots (
                product_id, store_id, crawled_at, crawl_date, price, listed_price, in_stock, reviews
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (product_id, store_id, crawl_date) DO UPDATE SET
                price = EXCLUDED.price,
                listed_price = EXCLUDED.listed_price,
                in_stock = EXCLUDED.in_stock,
                reviews = EXCLUDED.reviews;
            """

            for _, r in df_load.iterrows():
                p_id = int(r["product_id"])
                s_id = int(r["store_id"])
                crawled_at = r["crawled_at"].to_pydatetime() if hasattr(r["crawled_at"], "to_pydatetime") else r["crawled_at"]
                crawl_date = r["crawl_date"]
                price = int(r["price"])
                listed_price = int(r["listed_price"]) if pd.notna(r["listed_price"]) else None
                in_stock = True
                reviews = 0

                cur.execute(
                    upsert_sql,
                    (p_id, s_id, crawled_at, crawl_date, price, listed_price, in_stock, reviews)
                )
                if cur.rowcount == 1:
                    inserted += 1
                else:
                    updated += 1

            conn.commit()

    print(f"[Load] Inserted: {inserted}, Updated: {updated}")
    return inserted, updated


# ============================================================
# MAIN
# ============================================================
def run():
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    run_start = datetime.now(timezone.utc)
    print("=" * 60)
    print(f"ETL started: {datetime.now()}")
    print("=" * 60)

    try:
        df = extract(since_hours=48)
        if len(df) == 0:
            print("Khong co du lieu moi. Bo qua.")
            log_run("success", 0, None, run_start)
            return

        df = clean(df)
        df = normalize(df)

        errors = validate(df)
        if errors:
            err_msg = "; ".join(errors)
            log_run("failed", len(df), err_msg, run_start)
            print(f"[ERROR] {err_msg}")
            sys.exit(1)

        inserted, updated = load(df)
        total_processed = inserted + updated
        log_run("success", total_processed, None, run_start)
        print(f"ETL finished successfully: {datetime.now()} (Tong xu ly: {total_processed} snapshots)")

    except Exception as e:
        print(f"[FATAL] ETL loi: {e}")
        log_run("failed", 0, str(e), run_start)
        sys.exit(1)


if __name__ == "__main__":
    run()
