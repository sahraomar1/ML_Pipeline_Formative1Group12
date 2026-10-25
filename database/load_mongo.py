# Loads the cleaned parquet file into a MongoDB collection.
# run from the repo root:  python database/load_mongo.py
import pandas as pd
from pymongo import MongoClient, ASCENDING
from config import DATA_PATH, MONGO_URI, MONGO_DB, MONGO_COLLECTION


def clean(value):
    # pandas uses NaN for missing, mongo should get None (null) instead
    return None if pd.isna(value) else value


def num(value):
    # same as clean but for numbers, also rounds away the float noise (8.970000000000027)
    return None if pd.isna(value) else round(float(value), 2)


def main():
    df = pd.read_parquet(DATA_PATH)

    # same cleaning as the SQL loader: drop the empty hours, fix the casing
    df = df[df["traffic_volume"].notna()].reset_index()
    df["weather_description"] = df["weather_description"].str.lower().str.strip()

    docs = []
    for r in df.itertuples(index=False):
        docs.append({
            "timestamp": r.date_time.to_pydatetime(),
            "traffic_volume": int(r.traffic_volume),
            "weather": {
                "main": r.weather_main,
                "description": r.weather_description,
                "temp_c": num(r.temp_c),
                "rain_1h": num(r.rain_1h),
                "snow_1h": num(r.snow_1h),
                "clouds_all": num(r.clouds_all),
            },
            "holiday": clean(r.holiday),
        })

    client = MongoClient(MONGO_URI)
    col = client[MONGO_DB][MONGO_COLLECTION]
    col.drop()  # start fresh so we can re-run the script

    for i in range(0, len(docs), 5000):
        col.insert_many(docs[i:i + 5000])

    # unique index on the timestamp, this makes date range queries fast
    col.create_index([("timestamp", ASCENDING)], unique=True)

    print("documents inserted:", col.count_documents({}))


if __name__ == "__main__":
    main()