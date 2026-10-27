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


# =====================================================================
# MySQL CRUD  (table: traffic_records, PK: record_id, order: record_time)
# =====================================================================
MYSQL_COLUMNS = (
    "record_id, record_time, traffic_volume, temp_c, rain_1h, "
    "snow_1h, clouds_all, weather_id, holiday_id"
)


@app.post("/mysql/records", status_code=201)
def create_mysql_record(record: TrafficRecordIn):
    sql = text(f"""
        INSERT INTO traffic_records
            (record_time, traffic_volume, temp_c, rain_1h, snow_1h,
             clouds_all, weather_id, holiday_id)
        VALUES (:record_time, :traffic_volume, :temp_c, :rain_1h, :snow_1h,
                :clouds_all, :weather_id, :holiday_id)
    """)
    try:
        with mysql_engine.begin() as conn:
            result = conn.execute(sql, record.model_dump())
            new_id = result.lastrowid
        return {"message": "Record created", "record_id": new_id}
    except Exception as exc:
        raise HTTPException(500, "MySQL insert failed") from exc


@app.get("/mysql/records")
def list_mysql_records():
    sql = text(f"SELECT {MYSQL_COLUMNS} FROM traffic_records ORDER BY record_time DESC")
    try:
        with mysql_engine.connect() as conn:
            rows = conn.execute(sql).mappings().all()
        return [dict(row) for row in rows]
    except Exception as exc:
        raise HTTPException(500, "MySQL read failed") from exc


@app.get("/mysql/records/latest")
def latest_mysql_record():
    sql = text(f"SELECT {MYSQL_COLUMNS} FROM traffic_records ORDER BY record_time DESC LIMIT 1")
    try:
        with mysql_engine.connect() as conn:
            row = conn.execute(sql).mappings().first()
        if row is None:
            raise HTTPException(404, "No records found")
        return dict(row)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(500, "MySQL query failed") from exc


@app.get("/mysql/records/range")
def mysql_records_by_range(start_date: str, end_date: str):
    start = parse_date(start_date)
    end = parse_date(end_date, end_of_day=True)
    if start > end:
        raise HTTPException(400, "Start date must not exceed end date")
    sql = text(f"""
        SELECT {MYSQL_COLUMNS}
        FROM traffic_records
        WHERE record_time >= :start AND record_time <= :end
        ORDER BY record_time ASC
    """)
    try:
        with mysql_engine.connect() as conn:
            rows = conn.execute(sql, {"start": start, "end": end}).mappings().all()
        return [dict(row) for row in rows]
    except Exception as exc:
        raise HTTPException(500, "MySQL query failed") from exc


@app.get("/mysql/records/{record_id}")
def get_mysql_record(record_id: int):
    sql = text(f"SELECT {MYSQL_COLUMNS} FROM traffic_records WHERE record_id = :id")
    try:
        with mysql_engine.connect() as conn:
            row = conn.execute(sql, {"id": record_id}).mappings().first()
        if row is None:
            raise HTTPException(404, "Record not found")
        return dict(row)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(500, "MySQL read failed") from exc


@app.put("/mysql/records/{record_id}")
def update_mysql_record(record_id: int, record: TrafficRecordIn):
    sql = text("""
        UPDATE traffic_records
        SET record_time = :record_time, traffic_volume = :traffic_volume,
            temp_c = :temp_c, rain_1h = :rain_1h, snow_1h = :snow_1h,
            clouds_all = :clouds_all, weather_id = :weather_id,
            holiday_id = :holiday_id
        WHERE record_id = :record_id
    """)
    try:
        with mysql_engine.begin() as conn:
            result = conn.execute(sql, {**record.model_dump(), "record_id": record_id})
        if result.rowcount == 0:
            raise HTTPException(404, "Record not found")
        return {"message": "Record updated", "record_id": record_id}
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(500, "MySQL update failed") from exc


@app.delete("/mysql/records/{record_id}")
def delete_mysql_record(record_id: int):
    sql = text("DELETE FROM traffic_records WHERE record_id = :id")
    try:
        with mysql_engine.begin() as conn:
            result = conn.execute(sql, {"id": record_id})
        if result.rowcount == 0:
            raise HTTPException(404, "Record not found")
        return {"message": "Record deleted", "record_id": record_id}
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(500, "MySQL delete failed") from exc


# =====================================================================
# MongoDB CRUD + time-series  (collection: traffic_readings)
# =====================================================================
@app.post("/mongodb/records", status_code=201)
def create_mongo_record(record: MongoRecordIn):
    try:
        result = mongo_collection.insert_one(record.model_dump())
        return {"message": "Record created", "id": str(result.inserted_id)}
    except Exception as exc:
        raise HTTPException(500, "MongoDB insert failed") from exc


@app.get("/mongodb/records")
def list_mongo_records():
    try:
        docs = mongo_collection.find().sort("timestamp", -1)
        return [mongo_out(doc) for doc in docs]
    except Exception as exc:
        raise HTTPException(500, "MongoDB read failed") from exc


@app.get("/mongodb/records/latest")
def latest_mongo_record():
    try:
        doc = mongo_collection.find_one({}, sort=[("timestamp", -1), ("_id", -1)])
        if doc is None:
            raise HTTPException(404, "No records found")
        return mongo_out(doc)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(500, "MongoDB query failed") from exc


@app.get("/mongodb/records/range")
def mongo_records_by_range(start_date: str, end_date: str):
    start = parse_date(start_date)
    end = parse_date(end_date, end_of_day=True)
    if start > end:
        raise HTTPException(400, "Start date must not exceed end date")
    try:
        docs = mongo_collection.find(
            {"timestamp": {"$gte": start, "$lte": end}}
        ).sort("timestamp", 1)
        return [mongo_out(doc) for doc in docs]
    except Exception as exc:
        raise HTTPException(500, "MongoDB query failed") from exc


@app.get("/mongodb/records/{record_id}")
def get_mongo_record(record_id: str):
    if not ObjectId.is_valid(record_id):
        raise HTTPException(400, "Invalid MongoDB record ID")
    try:
        doc = mongo_collection.find_one({"_id": ObjectId(record_id)})
        if doc is None:
            raise HTTPException(404, "Record not found")
        return mongo_out(doc)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(500, "MongoDB read failed") from exc


@app.put("/mongodb/records/{record_id}")
def update_mongo_record(record_id: str, record: MongoRecordIn):
    if not ObjectId.is_valid(record_id):
        raise HTTPException(400, "Invalid MongoDB record ID")
    try:
        result = mongo_collection.update_one(
            {"_id": ObjectId(record_id)},
            {"$set": record.model_dump()},
        )
        if result.matched_count == 0:
            raise HTTPException(404, "Record not found")
        return {"message": "Record updated", "id": record_id}
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(500, "MongoDB update failed") from exc


@app.delete("/mongodb/records/{record_id}")
def delete_mongo_record(record_id: str):
    if not ObjectId.is_valid(record_id):
        raise HTTPException(400, "Invalid MongoDB record ID")
    try:
        result = mongo_collection.delete_one({"_id": ObjectId(record_id)})
        if result.deleted_count == 0:
            raise HTTPException(404, "Record not found")
        return {"message": "Record deleted", "id": record_id}
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(500, "MongoDB delete failed") from exc
