import argparse
import math
import sys
from datetime import timedelta
from pathlib import Path

import pandas as pd
import requests

ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT / "src"))
from features import MIN_HISTORY_HOURS, predict_next  # noqa: E402

MODEL_PATH = ROOT / "models" / "traffic_model_hgb_12.joblib"


class PipelineError(Exception):
    pass


def get_json(url, params=None):
    try:
        response = requests.get(url, params=params, timeout=30)
    except requests.exceptions.RequestException as exc:
        raise PipelineError(f"Could not reach the API at {url}. Is it running?") from exc
    if not response.ok:
        raise PipelineError(f"API returned HTTP {response.status_code} for {url}.")
    return response.json()


def to_frame(records, db):
    """Map MySQL or MongoDB field names to date_time, traffic_volume, holiday."""
    df = pd.DataFrame(records)
    if df.empty:
        raise PipelineError("The API returned no records for the requested date range.")
    if db == "mysql":
        df = df.rename(columns={"record_time": "date_time"})
        df["holiday"] = df["holiday_id"].apply(lambda x: None if pd.isna(x) else "holiday")
    else:
        df = df.rename(columns={"timestamp": "date_time"})
    df["date_time"] = pd.to_datetime(df["date_time"])
    df["traffic_volume"] = pd.to_numeric(df["traffic_volume"], errors="coerce")
    return df[["date_time", "traffic_volume", "holiday"]].sort_values("date_time")


def fetch_latest(api_url, db):
    record = get_json(f"{api_url}/{db}/records/latest")
    time_key = "record_time" if db == "mysql" else "timestamp"
    return pd.to_datetime(record[time_key]), record["traffic_volume"]


def fetch_history(api_url, db, latest_time):
    """Fetch whole days covering the 168 hours of history the model needs."""
    days = math.ceil(MIN_HISTORY_HOURS / 24) + 1
    params = {"start_date": (latest_time.normalize() - timedelta(days=days)).strftime("%Y-%m-%d"),
              "end_date": latest_time.strftime("%Y-%m-%d")}
    return to_frame(get_json(f"{api_url}/{db}/records/range", params), db)


def holidays_for(target):
    """The raw data labels only a holiday's first hour, so flag the target date here."""
    try:
        import holidays
    except ImportError:
        return []
    return [target.normalize()] if target.date() in holidays.US(years=target.year) else []


def forecast(history, hours):
    """Predict hour by hour; later hours reuse earlier predictions as history."""
    if not MODEL_PATH.exists():
        raise PipelineError(f"Model file not found: {MODEL_PATH}")
    target = history["date_time"].max() + pd.Timedelta(hours=1)
    results = []
    for _ in range(hours):
        try:
            value = predict_next(history, target, MODEL_PATH, holidays_for(target))
        except ValueError as exc:
            raise PipelineError(str(exc)) from exc
        results.append((target, value))
        row = pd.DataFrame({"date_time": [target], "traffic_volume": [value], "holiday": [None]})
        history = pd.concat([history, row], ignore_index=True)
        target += pd.Timedelta(hours=1)
    return results


def main():
    parser = argparse.ArgumentParser(description="Forecast traffic volume from the API.")
    parser.add_argument("--api-url", default="http://127.0.0.1:8000")
    parser.add_argument("--db", choices=["mysql", "mongodb"], default="mysql")
    parser.add_argument("--hours", type=int, default=1, help="hours ahead to forecast")
    args = parser.parse_args()
    if args.hours < 1:
        parser.error("--hours must be at least 1")
    api_url = args.api_url.rstrip("/")

    try:
        latest_time, latest_volume = fetch_latest(api_url, args.db)
        print(f"Latest record ({args.db}): {latest_time}, traffic_volume = {latest_volume}")
        history = fetch_history(api_url, args.db, latest_time)
        print(f"Fetched {len(history)} records: {history['date_time'].min()} to {history['date_time'].max()}")
        results = forecast(history, args.hours)
    except PipelineError as exc:
        sys.exit(f"Error: {exc}")

    print("Predicted traffic volume (vehicles per hour):")
    for when, value in results:
        print(f"  {when}  ->  {value:,.0f}")


if __name__ == "__main__":
    main()