# ML Pipeline_Formative1Group12: Hourly Traffic Volume (Time Series)

We use an hourly traffic dataset (traffic volume with weather and holiday information, from 2 Oct 2012 to 30 Sep 2018) to predict the traffic volume. The project covers data analysis and modelling, two databases (MySQL and MongoDB), an API, and a prediction script.

**Google Drive (data files):** https://drive.google.com/drive/folders/1-fGfodOH30hVsTVAOJizSYFNmXEpTTrT?usp=sharing

The data files are not stored in this repository. Download `traffic_clean_hourly.parquet` from the Drive link and put it in `data/processed/`.

## Project structure

| Folder / file | What it has |
|---|---|
| `traffic_volume_task1.ipynb` | Task 1: preprocessing, analysis and model |
| `database/` | Task 2: MySQL and MongoDB scripts, queries, ERD |
| `api/` | Task 3: FastAPI endpoints |
| `scripts/predict.py` | Task 4: prediction script |
| `src/features.py` | Feature code shared by the notebook and the prediction script |
| `models/` | The trained model (`traffic_model_hgb_12.joblib`) |
| `data/processed/` | Data files (not in the repository, see the Drive link) |
| `requirements.txt` | Python packages |
| `.env.example` | Example settings for the database passwords |

## Team

| Member | Task |
|---|---|
| Faith Irakoze | Task 1: Time-series preprocessing and exploratory analysis |
| Sahra Omar | Task 2: Design databases (SQL and MongoDB) |
| Peter Michael Angelo Rucakibungo | Task 3: CRUD endpoints and time-series queries |
| Junior Nkube Igiraneza | Task 4: Prediction/forecast script |

## Setup

You need Python, MySQL and MongoDB installed and running.

```
pip install -r requirements.txt
pip install pymysql pymongo
```

Run all commands from the main project folder.

## Task 1: Preprocessing, analysis and model

Dataset: Metro Interstate Traffic Volume (I-94, Minneapolis-St. Paul). It has 48,204 original records and 9 columns, with hourly data from 2 Oct 2012 to 30 Sep 2018. The target is traffic_volume (vehicles per hour).

Preprocessing (Task 1A)

7,629 repeated timestamps were combined into one row per hour.
A complete hourly timeline was created (52,551 hours). 11,976 hours (22.8%) were missing. Gaps of up to 6 hours were interpolated, and 8,928 hours in 76 longer gaps were left missing.
Invalid values were set to missing: a temperature of 0 K, an extreme rainfall value (about 9,831 mm), and 32 near-zero traffic hours on 23-24 July 2016 (suspected sensor or road-closure problem).
Temperature was converted from Kelvin to Celsius, and the holiday flags were rebuilt for the full holiday date.

Analytical questions (Task 1B)

Five questions were answered, each with visualizations and an interpretation:

Is there a long-term trend in traffic volume?
Are there daily and weekly patterns?
How do holidays affect traffic?
Are there lag effects (1, 24 and 168 hours earlier)?
Do moving averages show trends or unusual days?

Model (Task 1C)

The model predicts the traffic volume one hour ahead. The features are calendar information, previous traffic volumes (lags of 1, 24 and 168 hours), and shifted 24-hour and 7-day moving averages. The data was split by time: training up to December 2016, validation in 2017, and testing in 2018. A baseline, Ridge, Random Forest and HistGradientBoosting were compared, and hyperparameter experiments were run on HistGradientBoosting.

Experiment (validation)	MAE	RMSE	R²
Baseline: same hour last week	301.8	563.4	0.919
Ridge: calendar + lags	305.1	444.0	0.950
Random Forest: calendar + lags + moving averages	161.2	254.2	0.984
HistGradientBoosting (best settings)	155.6	243.1	0.985

The best settings were a learning rate of 0.1, a maximum depth of 8 and 500 iterations. The final model was trained on the training and validation data and tested on 2018: MAE 144.5, RMSE 223.7, R² 0.987. Lags and moving averages improved the predictions a lot, while the weather variables added very little. The full experiment table is in the notebook.

How to run the notebook

Download the Metro Interstate Traffic Volume CSV and upload traffic_volume_task1.ipynb to Google Colab.
Put the CSV in MyDrive/traffic_project/data/raw/ in Google Drive.
Run the cells in order, starting from the setup section. The notebook saves the processed data, figures and model.

## Task 2: Databases (MySQL and MongoDB)

Both databases use `data/processed/traffic_clean_hourly.parquet`. The files are in the `database/` folder.

**Files**

- `schema.sql` creates the MySQL database and 3 tables
- `load_mysql.py` puts the data into MySQL
- `queries_mysql.sql` has 6 SQL queries
- `load_mongo.py` puts the data into MongoDB
- `queries_mongo.py` has 6 MongoDB queries
- `sample_documents.json` has example MongoDB documents
- `ERD.png` is the diagram of the SQL tables
- `config.py` has the database settings

**The databases**

- MySQL has 3 tables: `traffic_records` (one row for each hour), `weather_types` and `holidays`.
- MongoDB has one collection called `traffic_readings`. Each document is one hour, with the weather values inside a `weather` object.
- The file has 52,551 hourly rows, but 8,928 hours are empty (no readings). Only the 43,623 hours with data are loaded.
- Weather descriptions are changed to lowercase before loading.

**How to run it**

1. Put the data file in `data/processed/traffic_clean_hourly.parquet`.
2. Create the MySQL tables:
   ```
   mysql -u root -p -e "source database/schema.sql"
   ```
3. Load the data into both databases (both should show 43623):
   ```
   python database/load_mysql.py
   python database/load_mongo.py
   ```
4. Run the queries:
   ```
   mysql -u root -p -t -e "source database/queries_mysql.sql"
   python database/queries_mongo.py
   ```

If your MySQL password or port is different, set `MYSQL_PASSWORD` and `MYSQL_PORT` on your computer before running the Python files. Don't write your password in `config.py`. If the `mysql` command is not found on Windows, use the full path to `mysql.exe`.

## Task 3: CRUD API and Time-Series Queries

### Overview

This component exposes API endpoints for managing the hourly traffic records stored in MySQL (`traffic_records`, `weather_types`, `holidays`) and MongoDB (`traffic_readings`), reusing the exact schema and connection config built in Task 2 (`database/schema.sql`, `database/config.py`). The API supports creating, retrieving, updating, and deleting records, as well as retrieving the latest record and filtering records by date range, for both databases.

### Technology Stack

- Python, FastAPI, Uvicorn
- MySQL via SQLAlchemy + PyMySQL
- MongoDB via PyMongo

### Endpoints

| Method | MySQL | MongoDB | Purpose |
|---|---|---|---|
| POST | `/mysql/records` | `/mongodb/records` | Create a record |
| GET | `/mysql/records` | `/mongodb/records` | Retrieve all records (newest first) |
| GET | `/mysql/records/{id}` | `/mongodb/records/{id}` | Retrieve one record |
| PUT | `/mysql/records/{id}` | `/mongodb/records/{id}` | Update a record |
| DELETE | `/mysql/records/{id}` | `/mongodb/records/{id}` | Delete a record |
| GET | `/mysql/records/latest` | `/mongodb/records/latest` | Retrieve the latest record |
| GET | `/mysql/records/range` | `/mongodb/records/range` | Retrieve records within a date range |

MySQL uses the auto-increment `record_id`. MongoDB uses its native ObjectId, returned/accepted as a string `id`.

### Running the API

1. `pip install -r api/requirements.txt`
2. Copy `.env.example` to `.env` and fill in your real MySQL/MongoDB credentials (these feed `database/config.py` via environment variables; `.env` itself is git-ignored).
3. From the repo root, run: `uvicorn api.main:app --reload`
4. Open http://127.0.0.1:8000/docs to inspect and test the API interactively.

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

### Limitations

This implementation assumes the Task 2 schema exactly as defined in `database/schema.sql` and `database/load_mongo.py`. Behaviour depends on both databases being reachable and populated, and MongoDB storing `timestamp` as a BSON date (already handled by `load_mongo.py`).

## Task 4: Prediction Script

`scripts/predict.py` fetches recent hourly records from the API, preprocesses them with the same feature pipeline as Task 1 (`src/features.py`), loads the trained model (`models/traffic_model_hgb_12.joblib`) and forecasts the next hour(s) of traffic volume. It needs about 8 days of history because the model uses lag and rolling-window features.

### How to run

1. Start MySQL, load the data (`database/schema.sql`, then `python database/load_mysql.py`) and set `MYSQL_PASSWORD` as an environment variable.
2. Terminal 1: `uvicorn api.main:app --reload`
3. Terminal 2: `python scripts/predict.py`

Optional flags: `--api-url`, `--db mysql|mongodb`, `--hours N`.
