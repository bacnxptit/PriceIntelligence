from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(
    title="PriceIntelli API",
    description="Backend API for Price Intelligence project (PostgreSQL + Scrapyd + ETL + ML Model)",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

from api import (
    db,
    read_products,
    read_timeseries,
    read_kpi,
    write,
    analytics,
    pipeline_audit,
    scrapyd_client,
    etl_trigger,
    ml_model,
)

app.include_router(read_products.router, prefix="/api/products", tags=["Products"])
app.include_router(read_timeseries.router, prefix="/api/timeseries", tags=["Time Series"])
app.include_router(read_kpi.router, prefix="/api/kpi", tags=["KPI"])
app.include_router(write.router, prefix="/api/write", tags=["Write"])
app.include_router(analytics.router, prefix="/api/analytics", tags=["Analytics"])
app.include_router(pipeline_audit.router, prefix="/api/pipeline", tags=["Pipeline"])
app.include_router(scrapyd_client.router, prefix="/api/scrapyd", tags=["Scrapyd"])
app.include_router(etl_trigger.router, prefix="/api/etl", tags=["ETL"])
app.include_router(ml_model.router, prefix="/api/ml", tags=["ML Model"])


@app.on_event("startup")
def on_startup():
    # Tu dong khoi tao view va bang can thiet tren database
    db.init_database_schema()


@app.get("/")
def health_check():
    return {
        "status": "ok",
        "service": "priceintelli-api",
        "version": "1.0.0",
        "docs_url": "/docs",
    }
