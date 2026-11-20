from fastapi import APIRouter, Query
from api.db import execute_query

router = APIRouter()


@router.get("/index")
def get_price_history_index(days: int = Query(90, le=365)):
    # Price index by store by day
    sql = """
    WITH base AS (
        SELECT store, MIN(crawl_date) AS base_date,
        FIRST_VALUE(price) OVER (PARTITION BY store ORDER BY crawl_date) AS base_price
        FROM iphone_clean_products
        GROUP BY store, price, crawl_date
    )
    SELECT f.crawl_date, f.store,
    AVG(f.price / NULLIF(b.base_price, 0) * 100) AS price_index
    FROM iphone_clean_products f
    JOIN base b ON b.store = f.store
    WHERE f.crawl_date >= CURRENT_DATE - INTERVAL '%(days)s days'
    GROUP BY f.crawl_date, f.store
    ORDER BY f.crawl_date ASC
    """
    df = execute_query(sql, {"days": days})
    return df.to_dict(orient="records")


@router.get("/product/{product_match_key}")
def get_price_history_by_product(
    product_match_key: str,
    days: int = Query(60, le=365),
):
    # Price history for one model
    sql = """
    SELECT crawl_date, AVG(price) AS avg_price, MIN(price) AS min_price, MAX(price) AS max_price
    FROM iphone_clean_products
    WHERE product_match_key = %(key)s
    AND crawl_date >= CURRENT_DATE - INTERVAL '%(days)s days'
    GROUP BY crawl_date
    ORDER BY crawl_date ASC
    """
    df = execute_query(sql, {"key": product_match_key, "days": days})
    return df.to_dict(orient="records")


@router.get("/market-stats")
def get_market_stats_timeline(days: int = Query(30, le=365)):
    # Min/max/avg by day
    sql = """
    SELECT crawl_date,
    MIN(price) AS market_min,
    MAX(price) AS market_max,
    AVG(price)::BIGINT AS market_avg,
    COUNT(DISTINCT store) AS store_count
    FROM iphone_clean_products
    WHERE crawl_date >= CURRENT_DATE - INTERVAL '%(days)s days'
    GROUP BY crawl_date
    ORDER BY crawl_date ASC
    """
    df = execute_query(sql, {"days": days})
    return df.to_dict(orient="records")
