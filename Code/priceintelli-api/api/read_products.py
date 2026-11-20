from fastapi import APIRouter, Query
from api.db import execute_query

router = APIRouter()


@router.get("/latest")
def get_latest_clean_products(limit: int = Query(1000, le=5000)):
    # Get latest products from iphone_clean_products
    sql = """
    SELECT * FROM iphone_clean_products
    WHERE crawl_date = (SELECT MAX(crawl_date) FROM iphone_clean_products)
    LIMIT %(limit)s
    """
    df = execute_query(sql, {"limit": limit})
    return df.to_dict(orient="records")


@router.get("/analytics/latest")
def get_latest_price_analytics(limit: int = Query(1000, le=5000)):
    # Get latest analytics from iphone_price_analytics
    sql = """
    SELECT * FROM iphone_price_analytics
    WHERE crawl_date = (SELECT MAX(crawl_date) FROM iphone_price_analytics)
    LIMIT %(limit)s
    """
    df = execute_query(sql, {"limit": limit})
    return df.to_dict(orient="records")


@router.get("/by-store/{store_name}")
def get_products_by_store(store_name: str):
    # Filter products by store name
    sql = """
    SELECT * FROM iphone_clean_products
    WHERE store = %(store)s
    AND crawl_date = (SELECT MAX(crawl_date) FROM iphone_clean_products)
    """
    df = execute_query(sql, {"store": store_name})
    return df.to_dict(orient="records")


@router.get("/by-model/{product_match_key}")
def get_products_by_model(product_match_key: str):
    # Filter products by model key
    sql = """
    SELECT * FROM iphone_clean_products
    WHERE product_match_key = %(key)s
    AND crawl_date = (SELECT MAX(crawl_date) FROM iphone_clean_products)
    ORDER BY price ASC
    """
    df = execute_query(sql, {"key": product_match_key})
    return df.to_dict(orient="records")


@router.get("/distribution/{product_match_key}")
def get_price_distribution(product_match_key: str):
    # Price distribution of a model across all stores
    sql = """
    SELECT store, price, listed_price, rating, reviews
    FROM iphone_clean_products
    WHERE product_match_key = %(key)s
    AND crawl_date = (SELECT MAX(crawl_date) FROM iphone_clean_products)
    ORDER BY price ASC
    """
    df = execute_query(sql, {"key": product_match_key})
    return df.to_dict(orient="records")


@router.get("/comparison/{product_match_key}")
def get_store_comparison(product_match_key: str):
    # Compare prices of same model across stores
    sql = """
    SELECT store, price, listed_price,
    (price - AVG(price) OVER ()) AS price_diff_vs_avg
    FROM iphone_clean_products
    WHERE product_match_key = %(key)s
    AND crawl_date = (SELECT MAX(crawl_date) FROM iphone_clean_products)
    ORDER BY price ASC
    """
    df = execute_query(sql, {"key": product_match_key})
    return df.to_dict(orient="records")
