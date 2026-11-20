import os
import subprocess
import sys
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()

# Tim duong dan tuyet doi den cac script neu duong dan tuong doi
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_ETL_PATH = os.path.abspath(os.path.join(BASE_DIR, "..", "priceintelli-etl", "etl_pipeline.py"))
DEFAULT_ANALYTICS_PATH = os.path.abspath(os.path.join(BASE_DIR, "..", "MatchingData", "bai5_price_analytics.py"))

ETL_SCRIPT_PATH = os.getenv("ETL_SCRIPT_PATH") or DEFAULT_ETL_PATH
if not os.path.isabs(ETL_SCRIPT_PATH):
    ETL_SCRIPT_PATH = os.path.abspath(os.path.join(BASE_DIR, ETL_SCRIPT_PATH))

ANALYTICS_SCRIPT_PATH = os.getenv("ANALYTICS_SCRIPT_PATH") or DEFAULT_ANALYTICS_PATH
if not os.path.isabs(ANALYTICS_SCRIPT_PATH):
    ANALYTICS_SCRIPT_PATH = os.path.abspath(os.path.join(BASE_DIR, ANALYTICS_SCRIPT_PATH))


@router.post("/run")
def trigger_etl_pipeline():
    # Trigger ETL script
    if not ETL_SCRIPT_PATH or not os.path.exists(ETL_SCRIPT_PATH):
        raise HTTPException(status_code=500, detail=f"ETL script not found at {ETL_SCRIPT_PATH}")

    result = subprocess.run(
        [sys.executable, ETL_SCRIPT_PATH],
        capture_output=True,
        text=True,
        timeout=600,
    )
    return {
        "status": "success" if result.returncode == 0 else "failed",
        "returncode": result.returncode,
        "stdout": result.stdout[-2000:],
        "stderr": result.stderr[-2000:],
    }


@router.post("/analytics")
def trigger_analytics_refresh():
    # Trigger analytics script
    if not ANALYTICS_SCRIPT_PATH or not os.path.exists(ANALYTICS_SCRIPT_PATH):
        raise HTTPException(status_code=500, detail=f"Analytics script not found at {ANALYTICS_SCRIPT_PATH}")

    result = subprocess.run(
        [sys.executable, ANALYTICS_SCRIPT_PATH],
        capture_output=True,
        text=True,
        timeout=600,
    )
    return {
        "status": "success" if result.returncode == 0 else "failed",
        "returncode": result.returncode,
        "stdout": result.stdout[-2000:],
        "stderr": result.stderr[-2000:],
    }


@router.post("/full-pipeline")
def trigger_full_pipeline():
    # Crawl then ETL then Analytics
    from api.scrapyd_client import SCRAPYD_URL, DEFAULT_PROJECT
    import requests

    spiders = [
        "apple_vn", "fptshop", "thegioididong", "topzone",
        "cellphones", "hoanghamobile", "viettelstore", "mobilecity"
    ]
    jobs = []
    for spider in spiders:
        try:
            resp = requests.post(
                f"{SCRAPYD_URL}/schedule.json",
                data={"project": DEFAULT_PROJECT, "spider": spider},
                timeout=10,
            )
            jobs.append(resp.json())
        except Exception as exc:
            jobs.append({"spider": spider, "status": "error", "message": str(exc)})

    return {"status": "scheduled", "jobs": jobs}
