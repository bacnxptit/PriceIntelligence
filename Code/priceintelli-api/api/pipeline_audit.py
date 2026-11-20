from typing import Optional
from fastapi import APIRouter, Query
from pydantic import BaseModel
from api.db import execute_query, execute_write

router = APIRouter()


class PipelineRunLog(BaseModel):
    job_name: str
    status: str
    records_processed: int = 0
    error_message: Optional[str] = None


@router.get("/runs")
def get_pipeline_runs(limit: int = Query(20, le=100)):
    # Pipeline run history
    sql = """
    SELECT * FROM pipeline_runs
    ORDER BY started_at DESC
    LIMIT %(limit)s
    """
    df = execute_query(sql, {"limit": limit})
    return df.to_dict(orient="records")


@router.post("/log")
def log_pipeline_run(log: PipelineRunLog):
    # Write ETL log
    sql = """
    INSERT INTO pipeline_runs
    (job_name, started_at, finished_at, status, records_processed, error_message)
    VALUES
    (%(job_name)s, NOW(), NOW(), %(status)s, %(records)s, %(error)s)
    """
    rowcount = execute_write(
        sql,
        {
            "job_name": log.job_name,
            "status": log.status,
            "records": log.records_processed,
            "error": log.error_message,
        },
    )
    return {"status": "ok", "rowcount": rowcount}


@router.get("/records-by-date")
def get_records_by_date(days: int = Query(7, le=30)):
    # Records count by date
    sql = """
    SELECT crawl_date, COUNT(*) AS records
    FROM iphone_clean_products
    WHERE crawl_date >= CURRENT_DATE - INTERVAL '%(days)s days'
    GROUP BY crawl_date
    ORDER BY crawl_date DESC
    """
    df = execute_query(sql, {"days": days})
    return df.to_dict(orient="records")
