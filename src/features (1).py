"""Feature pipeline shared by training (Task 1) and the prediction script (Task 4)."""
import joblib
import numpy as np
import pandas as pd

FEATURES = ["hour", "hour_sin", "hour_cos", "dayofweek", "month",
            "is_weekend_i", "is_holiday_i",
            "lag_1", "lag_24", "lag_168", "ma_24", "ma_168"]

MIN_HISTORY_HOURS = 168   # lag_168 and ma_168 need a week of earlier traffic


def build_features(history, target_time=None, holiday_dates=None):
    """Turn raw traffic records into model features.

    history       DataFrame with columns date_time, traffic_volume
                  (optional: holiday). Duplicate timestamps are averaged.
    target_time   hour to predict. A row for it is appended with no traffic
                  value, so its lags and moving averages use only earlier hours.
                  If None, features are built for every hour in `history`.
    holiday_dates dates (any format pandas parses) that are holidays. Combined
                  with any dates found in a `holiday` column. Pass the target
                  date here, because history alone may not know it is a holiday.
    """
    df = history.copy()
    df["date_time"] = pd.to_datetime(df["date_time"])

    hol = set()
    if holiday_dates is not None and len(holiday_dates) > 0:
        hol |= set(pd.to_datetime(list(holiday_dates)).normalize())
    if "holiday" in df.columns:
        labelled = df["holiday"].notna() & (df["holiday"].astype(str).str.strip().str.lower() != "none")
        hol |= set(df.loc[labelled, "date_time"].dt.normalize())

    # one row per timestamp, then a complete hourly index so shift(N) = N hours back
    s = df.groupby("date_time")["traffic_volume"].mean().sort_index()
    end = s.index.max() if target_time is None else max(pd.Timestamp(target_time), s.index.max())
    s = s.reindex(pd.date_range(s.index.min(), end, freq="h"))
    s.index.name = "date_time"

    out = pd.DataFrame(index=s.index)
    out["hour"] = out.index.hour
    out["hour_sin"] = np.sin(2 * np.pi * out["hour"] / 24)
    out["hour_cos"] = np.cos(2 * np.pi * out["hour"] / 24)
    out["dayofweek"] = out.index.dayofweek
    out["month"] = out.index.month
    out["is_weekend_i"] = (out["dayofweek"] >= 5).astype(int)
    out["is_holiday_i"] = out.index.normalize().isin(list(hol)).astype(int)

    for lag in (1, 24, 168):
        out[f"lag_{lag}"] = s.shift(lag)
    out["ma_24"] = s.shift(1).rolling(24, min_periods=19).mean()
    out["ma_168"] = s.shift(1).rolling(168, min_periods=134).mean()
    out["traffic_volume"] = s
    return out


def predict_next(history, target_time, model_path, holiday_dates=None):
    """Predict traffic_volume for target_time (one hour after the last record)."""
    bundle = joblib.load(model_path)
    feats = build_features(history, target_time, holiday_dates)
    row = feats.loc[[pd.Timestamp(target_time)], bundle["features"]]
    if row.isna().any(axis=None):
        missing = row.columns[row.isna().any()].tolist()
        raise ValueError(f"Not enough history for {target_time}: missing {missing}. "
                         f"Provide at least {MIN_HISTORY_HOURS} hours before it.")
    return float(bundle["model"].predict(row)[0])
