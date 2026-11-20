import os
from typing import Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import requests

router = APIRouter()

SCRAPYD_URL = os.getenv("SCRAPYD_URL", "http://127.0.0.1:6800")
DEFAULT_PROJECT = "priceintelli"


class ScheduleRequest(BaseModel):
    spider_name: str
    project: str = DEFAULT_PROJECT


@router.get("/status")
def scrapyd_daemon_status():
    # Check if Scrapyd is alive
    try:
        resp = requests.get(f"{SCRAPYD_URL}/daemonstatus.json", timeout=5)
        return resp.json()
    except requests.ConnectionError:
        raise HTTPException(status_code=503, detail="Scrapyd not responding")


@router.get("/projects")
def scrapyd_list_projects():
    # List projects
    try:
        resp = requests.get(f"{SCRAPYD_URL}/listprojects.json", timeout=5)
        return resp.json()
    except requests.ConnectionError:
        raise HTTPException(status_code=503, detail="Scrapyd not responding")


@router.get("/spiders/{project}")
def scrapyd_list_spiders(project: str = DEFAULT_PROJECT):
    # List spiders in project
    try:
        resp = requests.get(
            f"{SCRAPYD_URL}/listspiders.json",
            params={"project": project},
            timeout=5,
        )
        return resp.json()
    except requests.ConnectionError:
        raise HTTPException(status_code=503, detail="Scrapyd not responding")


@router.post("/schedule")
def scrapyd_schedule_job(req: ScheduleRequest):
    # Schedule spider job
    try:
        resp = requests.post(
            f"{SCRAPYD_URL}/schedule.json",
            data={"project": req.project, "spider": req.spider_name},
            timeout=10,
        )
        return resp.json()
    except requests.ConnectionError:
        raise HTTPException(status_code=503, detail="Scrapyd not responding")


@router.post("/cancel")
def scrapyd_cancel_job(job_id: str, project: str = DEFAULT_PROJECT):
    # Cancel job
    try:
        resp = requests.post(
            f"{SCRAPYD_URL}/cancel.json",
            data={"project": project, "jobid": job_id},
            timeout=10,
        )
        return resp.json()
    except requests.ConnectionError:
        raise HTTPException(status_code=503, detail="Scrapyd not responding")


@router.get("/jobs/{project}")
def scrapyd_list_jobs(project: str = DEFAULT_PROJECT):
    # List pending/running/finished jobs
    try:
        resp = requests.get(
            f"{SCRAPYD_URL}/listjobs.json",
            params={"project": project},
            timeout=5,
        )
        return resp.json()
    except requests.ConnectionError:
        raise HTTPException(status_code=503, detail="Scrapyd not responding")
