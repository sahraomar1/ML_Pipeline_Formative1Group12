"""Task 3: CRUD + time-series API for the traffic dataset.

Reuses the Task 2 schema/config as-is:
  - MySQL  : traffic_records (PK record_id, order column record_time),
             weather_types, holidays  (see database/schema.sql)
  - MongoDB: traffic_readings collection (see database/load_mongo.py)

Run from the repo root:
    uvicorn api.main:app --reload
"""
import sys
from datetime import datetime, time
from pathlib import Path
from typing import Optional

from bson import ObjectId
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from pymongo import MongoClient
from sqlalchemy import create_engine, text

# reuse the exact connection settings created in Task 2, don't redefine them
sys.path.append(str(Path(__file__).resolve().parents[1]))
from database.config import MYSQL, MONGO_URI, MONGO_DB, MONGO_COLLECTION  # noqa: E402

app = FastAPI(title="Traffic Volume API - Task 3")

# ---------------------------------------------------------------- MySQL ----
MYSQL_URL = (
    f"mysql+pymysql://{MYSQL['user']}:{MYSQL['password']}@"
    f"{MYSQL['host']}:{MYSQL['port']}/{MYSQL['database']}"
)
mysql_engine = create_engine(MYSQL_URL, pool_pre_ping=True)

# -------------------------------------------------------------- MongoDB ----
mongo_client = MongoClient(MONGO_URI)
mongo_collection = mongo_client[MONGO_DB][MONGO_COLLECTION]


# ----------------------------------------------------------- Pydantic ------
class TrafficRecordIn(BaseModel):
    """Matches the traffic_records table from database/schema.sql."""
    record_time: datetime
    traffic_volume: int
    temp_c: Optional[float] = None
    rain_1h: Optional[float] = None
    snow_1h: Optional[float] = None
    clouds_all: Optional[int] = None
    weather_id: int
    holiday_id: Optional[int] = None


class WeatherInfo(BaseModel):
    main: str
    description: str
    temp_c: Optional[float] = None
    rain_1h: Optional[float] = None
    snow_1h: Optional[float] = None
    clouds_all: Optional[float] = None


class MongoRecordIn(BaseModel):
    """Matches the documents written by database/load_mongo.py."""
    timestamp: datetime
    traffic_volume: int
    weather: WeatherInfo
    holiday: Optional[str] = None


def parse_date(value: str, end_of_day: bool = False) -> datetime:
    try:
        d = datetime.strptime(value, "%Y-%m-%d")
    except ValueError as exc:
        raise HTTPException(400, f"Invalid date '{value}', expected YYYY-MM-DD") from exc
    return datetime.combine(d.date(), time.max) if end_of_day else d


def mongo_out(doc: dict) -> dict:
    doc = dict(doc)
    doc["id"] = str(doc.pop("_id"))
    return doc
