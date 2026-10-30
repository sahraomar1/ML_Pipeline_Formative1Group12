# Task 1: Time-Series Preprocessing, Exploratory Analysis and Modelling

## Project overview

This project analyzes the **Metro Interstate Traffic Volume** dataset, which contains hourly westbound traffic observations from Interstate 94 (I-94) near Minneapolis–St. Paul, Minnesota. The objective is to understand traffic patterns, investigate factors associated with traffic volume, and develop a machine learning model to predict traffic volume one hour ahead.

This README documents **Task 1 only**:
- Task 1A: Understanding and preprocessing the dataset
- Task 1B: Analytical questions and exploratory analysis
- Task 1C: Machine learning model development and evaluation

## Dataset

The dataset is the [Metro Interstate Traffic Volume dataset](https://www.kaggle.com/datasets/).

- **Time period:** 2 October 2012 – 30 September 2018
- **Original records:** 48,204
- **Columns:** 9
- **Frequency:** Hourly
- **Prediction target:** `traffic_volume` (vehicles per hour)

The variables include the observation timestamp, traffic volume, temperature, rainfall, snowfall, cloud coverage, weather conditions, weather descriptions, and holiday information.

Place the downloaded CSV file at:

```text
data/
└── raw/
    └── Metro_Interstate_Traffic_Volume.csv
```

## Task 1A — Understanding and preprocessing the dataset

The dataset was loaded into Pandas and examined using its shape, data types, descriptive statistics, and time range. The analysis identified repeated timestamps, missing hourly observations, and implausible measurements.

Key preprocessing decisions:

| Issue identified | Action taken |
|---|---|
| 7,629 repeated timestamps | Aggregated to one record per hour, using the mean for numerical columns and the first value for text columns |
| 11,976 missing hours after creating a complete hourly timeline | Interpolated gaps of up to 6 hours and left longer gaps missing |
| Temperature recorded as 0 K | Treated as an invalid sensor value and set to missing |
| Extreme rainfall value (approximately 9,831 mm) | Treated as an invalid measurement and set to missing |
| Temperature recorded in Kelvin | Converted to Celsius |
| Holiday information recorded only on the first hour of a holiday | Reconstructed holiday flags for the full holiday date |
| 32 near-zero traffic hours from 23–24 July 2016 | Set to missing as a suspected sensor or road-closure issue |

After reindexing, the hourly timeline contained 52,551 expected hours. There were 11,976 missing hours (22.8%). Short gaps were interpolated, while 8,928 hours in 76 longer gaps remained missing.

The numerical distributions and weather-category frequencies were also visualized and interpreted.

## Task 1B — Analytical questions

Five analytical questions were investigated. Each question is supported by visualizations and interpretation.

1. **Is there a long-term trend in traffic volume?**  
   Monthly average traffic volume and a 12-month rolling mean were examined. Months with less than 80% hourly coverage were excluded from the corrected trend analysis.

2. **What daily and weekly seasonal patterns occur?**  
   Average traffic volume was compared by hour of day and day of week, including weekday and weekend patterns.

3. **How do holidays affect traffic?**  
   Traffic patterns on holidays were compared with non-holiday patterns to examine changes in commuter peaks and overall traffic volume.

4. **Are there lag effects in traffic volume?**  
   Traffic volume was compared with its values 1, 24, and 168 hours earlier. Correlations were also examined after removing the average weekday-hour pattern.

5. **Do moving averages reveal trends or unusual days?**  
   Trailing 24-hour and 7-day moving averages were used to identify deviations from typical traffic patterns and investigate unusual low-traffic days.

## Task 1C — Machine learning model

The modelling task is framed as **one-hour-ahead prediction**: predict traffic volume at hour *t* using information available up to hour *t − 1*.

The features include calendar information, previous traffic-volume values (lags of 1, 24, and 168 hours), and shifted 24-hour and 7-day moving averages. Weather variables were also tested in the initial experiments.

The data was split chronologically to prevent future observations from leaking into training:

- **Training set:** through December 2016
- **Validation set:** 2017
- **Test set:** 2018

The notebook compares baseline predictions, Ridge Regression, Random Forest, and HistGradientBoosting. Hyperparameter experiments were conducted for the HistGradientBoosting model.

### Validation results

| Experiment | MAE | RMSE | R² |
|---|---:|---:|---:|
| Baseline: repeat last hour | 596.6 | 834.7 | 0.822 |
| Baseline: same hour last week | 301.8 | 563.4 | 0.919 |
| Ridge: calendar + lags | 305.1 | 444.0 | 0.950 |
| Random Forest: calendar only | 258.7 | 387.9 | 0.962 |
| Random Forest: calendar + lags + moving averages | 161.2 | 254.2 | 0.984 |
| Random Forest: all features, including weather | 161.1 | 254.1 | 0.984 |
| **HistGradientBoosting: best configuration** | **155.6** | **243.1** | **0.985** |

The best validation configuration used a learning rate of 0.1, maximum depth of 8, and 500 iterations.

The final model was trained on the combined training and validation data and evaluated on the 2018 test set:

- **MAE:** 144.5
- **RMSE:** 223.7
- **R²:** 0.987

The experiments showed that adding lag features and moving averages substantially improved prediction performance. Weather variables provided little additional improvement in the tested experiments.

## Tools and libraries

- Python
- Pandas
- NumPy
- Matplotlib
- Seaborn
- Scikit-learn
- SciPy
- Joblib
- Google Colab and Google Drive

## How to run the notebook

1. Download the Metro Interstate Traffic Volume CSV dataset.
2. Upload `traffic_volume_task1.ipynb` to Google Colab.
3. Create the following folder in Google Drive: `MyDrive/traffic_project/data/raw/`.
4. Place `Metro_Interstate_Traffic_Volume.csv` inside the `raw` folder.
5. Run the notebook cells in order, starting from the setup section.

The notebook creates the required project folders and saves processed data and figures as the relevant sections run.

## Expected project structure

```text
traffic_project/
├── data/
│   ├── raw/
│   │   └── Metro_Interstate_Traffic_Volume.csv
│   └── processed/
├── figures/
├── models/
└── traffic_volume_task1.ipynb
```

## Notes

- Long missing-data gaps are deliberately retained rather than filled with potentially misleading interpolated values.
- The chronological train/validation/test split preserves the time order of the observations.
- Model metrics are reported from the notebook's validation and test evaluations.
- The notebook includes a separate handoff section after Task 1C; that section is outside the scope of this Task 1 README.
