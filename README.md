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
To be filled in after running the endpoints against the group's live MySQL/MongoDB instances: record create/read/update/delete results plus `latest` and `range` responses for both databases.

### Limitations
This implementation assumes the Task 2 schema exactly as defined in `database/schema.sql` and `database/load_mongo.py`. Behaviour depends on both databases being reachable and populated, and MongoDB storing `timestamp` as a BSON date (already handled by `load_mongo.py`).
