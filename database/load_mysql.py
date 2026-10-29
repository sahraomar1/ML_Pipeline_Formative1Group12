# Loads the cleaned parquet file into the MySQL tables.
# run from the repo root:  python database/load_mysql.py
import pandas as pd
import pymysql
from config import DATA_PATH, MYSQL


def main():
    df = pd.read_parquet(DATA_PATH)

    # the file has a full hourly grid, so hours with no reading are empty rows.
    # we only store the hours that actually have data
    df = df[df["traffic_volume"].notna()].reset_index()

    # "sky is clear" and "Sky is Clear" both exist, same thing with different casing.
    # MySQL treats them as duplicates, so make everything lowercase
    df["weather_description"] = df["weather_description"].str.lower().str.strip()
    print("rows to load:", len(df))

    conn = pymysql.connect(**MYSQL)
    cur = conn.cursor()

    # start fresh so the script can be run more than once
    cur.execute("DELETE FROM traffic_records")
    cur.execute("DELETE FROM weather_types")
    cur.execute("DELETE FROM holidays")

    # lookup table 1: weather types
    pairs = df[["weather_main", "weather_description"]].drop_duplicates()
    cur.executemany(
        "INSERT INTO weather_types (weather_main, weather_description) VALUES (%s, %s)",
        pairs.values.tolist(),
    )

    # lookup table 2: holidays
    names = df["holiday"].dropna().unique().tolist()
    cur.executemany("INSERT INTO holidays (holiday_name) VALUES (%s)", [(n,) for n in names])
    conn.commit()

    # get the generated ids back so we can use them as foreign keys
    cur.execute("SELECT weather_id, weather_main, weather_description FROM weather_types")
    weather_ids = {(m, d): i for i, m, d in cur.fetchall()}
    cur.execute("SELECT holiday_id, holiday_name FROM holidays")
    holiday_ids = {n: i for i, n in cur.fetchall()}

    rows = []
    for r in df.itertuples(index=False):
        rows.append((
            r.date_time.to_pydatetime(),
            int(r.traffic_volume),
            None if pd.isna(r.temp_c) else float(r.temp_c),
            None if pd.isna(r.rain_1h) else float(r.rain_1h),
            None if pd.isna(r.snow_1h) else float(r.snow_1h),
            None if pd.isna(r.clouds_all) else int(r.clouds_all),
            weather_ids[(r.weather_main, r.weather_description)],
            None if pd.isna(r.holiday) else holiday_ids[r.holiday],
        ))

    sql = """INSERT INTO traffic_records
             (record_time, traffic_volume, temp_c, rain_1h, snow_1h,
              clouds_all, weather_id, holiday_id)
             VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"""
    # insert in chunks so it doesn't take forever
    for i in range(0, len(rows), 5000):
        cur.executemany(sql, rows[i:i + 5000])
    conn.commit()

    for t in ["weather_types", "holidays", "traffic_records"]:
        cur.execute(f"SELECT COUNT(*) FROM {t}")
        print(t, cur.fetchone()[0])
    conn.close()


if __name__ == "__main__":
    main()