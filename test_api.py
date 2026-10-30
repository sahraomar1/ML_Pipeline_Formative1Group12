"""Manual end-to-end test script for Task 3 API, run against the live local
MySQL + MongoDB instances. Prints each request/response for the report.

Requires: pip install requests
Requires: the API running at http://127.0.0.1:8000 (uvicorn api.main:app)
Requires: a weather_types row with weather_id=1 (see README/testing notes)
"""
import json
import requests

BASE = "http://127.0.0.1:8000"


def show(title, resp):
    print(f"\n=== {title} ===")
    print(f"Status: {resp.status_code}")
    try:
        print(json.dumps(resp.json(), indent=2, default=str))
    except Exception:
        print(resp.text)


# ---------------------------------------------------------------- MySQL ----
mysql_payload = {
    "record_time": "2026-01-10T14:30:00",
    "traffic_volume": 4200,
    "temp_c": 12.5,
    "rain_1h": 0.0,
    "snow_1h": 0.0,
    "clouds_all": 20,
    "weather_id": 1,
    "holiday_id": None,
}
r = requests.post(f"{BASE}/mysql/records", json=mysql_payload)
show("MySQL CREATE", r)
mysql_id = r.json().get("record_id")

r = requests.get(f"{BASE}/mysql/records")
show("MySQL READ ALL", r)

r = requests.get(f"{BASE}/mysql/records/{mysql_id}")
show("MySQL READ ONE", r)

mysql_update = {**mysql_payload, "traffic_volume": 5000}
r = requests.put(f"{BASE}/mysql/records/{mysql_id}", json=mysql_update)
show("MySQL UPDATE", r)

r = requests.get(f"{BASE}/mysql/records/{mysql_id}")
show("MySQL READ AFTER UPDATE", r)

r = requests.get(f"{BASE}/mysql/records/latest")
show("MySQL LATEST", r)

r = requests.get(f"{BASE}/mysql/records/range", params={"start_date": "2026-01-01", "end_date": "2026-01-31"})
show("MySQL RANGE", r)

r = requests.delete(f"{BASE}/mysql/records/{mysql_id}")
show("MySQL DELETE", r)

r = requests.get(f"{BASE}/mysql/records/{mysql_id}")
show("MySQL READ AFTER DELETE (expect 404)", r)


# -------------------------------------------------------------- MongoDB ----
mongo_payload = {
    "timestamp": "2026-01-10T14:30:00",
    "traffic_volume": 4200,
    "weather": {
        "main": "Clear",
        "description": "sky is clear",
        "temp_c": 12.5,
        "rain_1h": 0.0,
        "snow_1h": 0.0,
        "clouds_all": 20,
    },
    "holiday": None,
}
r = requests.post(f"{BASE}/mongodb/records", json=mongo_payload)
show("Mongo CREATE", r)
mongo_id = r.json().get("id")

r = requests.get(f"{BASE}/mongodb/records")
show("Mongo READ ALL", r)

r = requests.get(f"{BASE}/mongodb/records/{mongo_id}")
show("Mongo READ ONE", r)

mongo_update = {**mongo_payload, "traffic_volume": 5000}
r = requests.put(f"{BASE}/mongodb/records/{mongo_id}", json=mongo_update)
show("Mongo UPDATE", r)

r = requests.get(f"{BASE}/mongodb/records/{mongo_id}")
show("Mongo READ AFTER UPDATE", r)

r = requests.get(f"{BASE}/mongodb/records/latest")
show("Mongo LATEST", r)

r = requests.get(f"{BASE}/mongodb/records/range", params={"start_date": "2026-01-01", "end_date": "2026-01-31"})
show("Mongo RANGE", r)

r = requests.delete(f"{BASE}/mongodb/records/{mongo_id}")
show("Mongo DELETE", r)

r = requests.get(f"{BASE}/mongodb/records/{mongo_id}")
show("Mongo READ AFTER DELETE (expect 404)", r)
