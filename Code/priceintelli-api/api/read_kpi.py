from fastapi import APIRouter
from api.db import execute_query

router = APIRouter()


@router.get("/dashboard")
def get_dashboard_kpis():
    # Dashboard KPI cards
    sql = """
    SELECT
        COUNT(*) AS total_products,
        COUNT(DISTINCT store) AS total_stores,
        SUM(CASE WHEN discount_pct > 8 THEN 1 ELSE 0 END) AS increased_products,
        SUM(CASE WHEN discount_pct <= 8 THEN 1 ELSE 0 END) AS decreased_products,
        SUM(CASE WHEN in_stock = FALSE THEN 1 ELSE 0 END) AS out_of_stock
    FROM iphone_clean_products
    WHERE crawl_date = (SELECT MAX(crawl_date) FROM iphone_clean_products)
    """
    df = execute_query(sql)
    records = df.to_dict(orient="records")
    return records[0] if records else {}


@router.get("/position-counts")
def get_position_counts():
    # Count products by price position
    sql = """
    SELECT price_position, COUNT(*) AS count
    FROM iphone_price_analytics
    WHERE crawl_date = (SELECT MAX(crawl_date) FROM iphone_price_analytics)
    GROUP BY price_position
    """
    df = execute_query(sql)
    return df.to_dict(orient="records")


@router.get("/company-match-rate")
def get_company_match_rate():
    # Match rate by store
    sql = """
    SELECT store,
        COUNT(DISTINCT product_match_key) AS matched_products,
        (SELECT COUNT(DISTINCT product_match_key)
         FROM iphone_clean_products
         WHERE crawl_date = (SELECT MAX(crawl_date) FROM iphone_clean_products)) AS total_products
    FROM iphone_clean_products
    WHERE crawl_date = (SELECT MAX(crawl_date) FROM iphone_clean_products)
    GROUP BY store
    ORDER BY matched_products DESC
    """
    df = execute_query(sql)
    if not df.empty and "total_products" in df.columns:
        df["match_rate"] = (df["matched_products"] / df["total_products"].replace(0, 1) * 100).round(1)
    return df.to_dict(orient="records")


@router.get("/correlation")
def get_correlation_matrix():
    # Correlation matrix
    sql = """
    SELECT price, listed_price, discount_pct, rating, reviews
    FROM iphone_clean_products
    WHERE crawl_date = (SELECT MAX(crawl_date) FROM iphone_clean_products)
    """
    df = execute_query(sql)
    if df.empty:
        return {"columns": [], "matrix": []}
    corr = df.corr().round(2)
    return {
        "columns": corr.columns.tolist(),
        "matrix": corr.values.tolist(),
    }
