from typing import List, Optional
from fastapi import APIRouter, Query
from pydantic import BaseModel
from api.db import execute_query

router = APIRouter()


class FilterCondition(BaseModel):
    field: str
    op: str
    min_val: Optional[float] = None
    max_val: Optional[float] = None


class FilterRequest(BaseModel):
    filters: List[FilterCondition]
    limit: int = 1000


@router.post("/filter")
def filter_products(req: FilterRequest):
    # Dynamic filter on SQL
    conditions = []
    params = {}
    col_map = {
        "Price": "price",
        "Rating": "rating",
        "Reviews": "reviews",
        "Discount %": "discount_pct",
    }

    for i, f in enumerate(req.filters):
        col = col_map.get(f.field, f.field)
        if f.op == "between" and f.min_val is not None and f.max_val is not None:
            conditions.append(f"{col} BETWEEN %(min_{i})s AND %(max_{i})s")
            params[f"min_{i}"] = f.min_val
            params[f"max_{i}"] = f.max_val
        elif f.op == ">" and f.min_val is not None:
            conditions.append(f"{col} > %(min_{i})s")
            params[f"min_{i}"] = f.min_val
        elif f.op == "<" and f.max_val is not None:
            conditions.append(f"{col} < %(max_{i})s")
            params[f"max_{i}"] = f.max_val
        elif f.op == "=" and f.min_val is not None:
            conditions.append(f"{col} = %(min_{i})s")
            params[f"min_{i}"] = f.min_val

    where = " AND ".join(conditions) if conditions else "1=1"
    sql = f"""
    SELECT * FROM iphone_clean_products
    WHERE crawl_date = (SELECT MAX(crawl_date) FROM iphone_clean_products)
    AND {where}
    LIMIT %(limit)s
    """
    params["limit"] = req.limit
    df = execute_query(sql, params)
    return df.to_dict(orient="records")


@router.get("/export")
def export_products_to_csv(limit: int = Query(10000, le=50000)):
    # Export full dataset
    sql = """
    SELECT * FROM iphone_clean_products
    WHERE crawl_date = (SELECT MAX(crawl_date) FROM iphone_clean_products)
    LIMIT %(limit)s
    """
    df = execute_query(sql, {"limit": limit})
    csv_data = df.to_csv(index=False)
    return {"csv": csv_data, "row_count": len(df)}
