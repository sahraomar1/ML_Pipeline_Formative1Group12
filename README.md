# ML_Pipeline_Formative1Group12

## Task 3: CRUD API and Time-Series Queries

### Overview
This component exposes API endpoints for managing the hourly traffic records stored in MySQL (`traffic_records`, `weather_types`, `holidays`) and MongoDB (`traffic_readings`), reusing the exact schema and connection config built in Task 2 (`database/schema.sql`, `database/config.py`). The API supports creating, retrieving, updating, and deleting records, as well as retrieving the latest record and filtering records by date range, for both databases.

### Technology Stack
- Python, FastAPI, Uvicorn
- MySQL via SQLAlchemy + PyMySQL
- MongoDB via PyMongo

### Endpoints

| Method | MySQL                   | MongoDB                   | Purpose                              |
| ------ | ----------------------- | -------------------------- | ------------------------------------ |
| POST   | `/mysql/records`        | `/mongodb/records`        | Create a record                      |
| GET    | `/mysql/records`        | `/mongodb/records`        | Retrieve all records (newest first)  |
| GET    | `/mysql/records/{id}`   | `/mongodb/records/{id}`   | Retrieve one record                  |
| PUT    | `/mysql/records/{id}`   | `/mongodb/records/{id}`   | Update a record                      |
| DELETE | `/mysql/records/{id}`   | `/mongodb/records/{id}`   | Delete a record                      |
| GET    | `/mysql/records/latest` | `/mongodb/records/latest` | Retrieve the latest record           |
| GET    | `/mysql/records/range`  | `/mongodb/records/range`  | Retrieve records within a date range |

MySQL uses the auto-increment `record_id`. MongoDB uses its native `ObjectId`, returned/accepted as a string `id`.

### Running the API
1. `pip install -r api/requirements.txt`
2. Copy `.env.example` to `.env` and fill in your real MySQL/MongoDB credentials (these feed `database/config.py` via environment variables; `.env` itself is git-ignored).
3. From the repo root, run: `uvicorn api.main:app --reload`
4. Open `http://127.0.0.1:8000/docs` to inspect and test the API interactively.

### Testing
All 14 endpoints were tested end-to-end against live local MySQL 8.4 and MongoDB instances (schema from `database/schema.sql`, one seeded `weather_types` row). A test record was created, read, updated, read again to confirm the update, queried via `latest` and `range`, deleted, then re-read to confirm the delete.

| Test | MySQL | MongoDB |
| ---- | ----- | ------- |
| Create (POST)            | 201, `record_id: 1` | 201, `id: 6ae4ebaf70b1aa6062e771d7` |
| Read all (GET)           | 200, new record present | 200, new document present |
| Read one (GET /{id})     | 200, `traffic_volume: 4200` | 200, `traffic_volume: 4200` |
| Update (PUT)             | 200, "Record updated" | 200, "Record updated" |
| Read after update        | 200, `traffic_volume: 5000` | 200, `traffic_volume: 5000` |
| Latest (GET)             | 200, returns the updated record | 200, returns the updated record |
| Range (GET, Jan 2026)    | 200, record included | 200, record included |
| Delete (DELETE)          | 200, "Record deleted" | 200, "Record deleted" |
| Read after delete        | 404, "Record not found" | 404, "Record not found" |

All CRUD operations and both time-series queries (`latest`, `range`) returned the expected status codes and data for both databases.

### Limitations
This implementation assumes the Task 2 schema exactly as defined in `database/schema.sql` and `database/load_mongo.py`. Behaviour depends on both databases being reachable and populated, and MongoDB storing `timestamp` as a BSON date (already handled by `load_mongo.py`).
