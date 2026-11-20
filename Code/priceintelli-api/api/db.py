import os
from contextlib import contextmanager
from dotenv import load_dotenv
import pandas as pd
import psycopg

load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"))
load_dotenv()

POSTGRES_URL = (
    os.getenv("POSTGRES_URL")
    or os.getenv("SUPABASE_DB_URL")
    or os.getenv("DATABASE_URL")
)


def _get_clean_url() -> str:
    url = POSTGRES_URL or ""
    if url.startswith("postgresql+psycopg://"):
        url = "postgresql://" + url.removeprefix("postgresql+psycopg://")
    return url


@contextmanager
def get_connection():
    # Context manager for psycopg connection
    db_url = _get_clean_url()
    if not db_url:
        raise ValueError("Thieu bien moi truong POSTGRES_URL / SUPABASE_DB_URL")
    conn = psycopg.connect(
        db_url,
        prepare_threshold=None,
        sslmode=os.getenv("PGSSLMODE", "require"),
    )
    try:
        yield conn
    finally:
        conn.close()


def execute_query(sql: str, params: dict = None) -> pd.DataFrame:
    # Run SELECT, return DataFrame
    with get_connection() as conn:
        return pd.read_sql(sql, conn, params=params)


def execute_write(sql: str, params: dict = None) -> int:
    # Run INSERT/UPDATE/DELETE, return rowcount
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            conn.commit()
            return cur.rowcount


def test_connection() -> dict:
    # Test database connection
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT version()")
                version = cur.fetchone()[0]
                return {"status": "ok", "version": version[:50]}
    except Exception as e:
        return {"status": "error", "message": str(e)}


def init_database_schema():
    """Khoi tao cac bang va view can thiet de API hoat dong lien mach"""
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                # 1. Bang pipeline_runs ghi log
                cur.execute("""
                CREATE TABLE IF NOT EXISTS pipeline_runs (
                    id SERIAL PRIMARY KEY,
                    job_name VARCHAR(100),
                    started_at TIMESTAMPTZ DEFAULT NOW(),
                    finished_at TIMESTAMPTZ DEFAULT NOW(),
                    status VARCHAR(50),
                    records_processed INT DEFAULT 0,
                    error_message TEXT
                );
                """)

                # 2. Tao view iphone_clean_products neu clean_products da ton tai
                cur.execute("""
                DO $$
                BEGIN
                    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'clean_products') THEN
                        EXECUTE 'CREATE OR REPLACE VIEW iphone_clean_products AS
                        SELECT 
                            id, 
                            title, 
                            "ID" AS product_id, 
                            brand, 
                            model, 
                            capacity_gb, 
                            product_match_key, 
                            store, 
                            price, 
                            listed_price, 
                            CASE 
                                WHEN listed_price > 0 AND listed_price >= price 
                                THEN ROUND(((listed_price - price)::numeric / listed_price * 100), 2)
                                ELSE 0 
                            END AS discount_pct,
                            COALESCE(rating, 5.0) AS rating, 
                            COALESCE(reviews, 0) AS reviews,
                            TRUE AS in_stock,
                            crawled_at, 
                            crawl_date, 
                            url
                        FROM clean_products;';
                    END IF;
                END
                $$;
                """)
                conn.commit()
    except Exception as exc:
        print(f"[Warning] Khong the khoi tao helper schema: {exc}")
