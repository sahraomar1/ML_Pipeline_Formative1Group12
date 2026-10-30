-- Task 2: SQL queries (run after load_mysql.py)
USE traffic_db;

SELECT t.record_time, t.traffic_volume, t.temp_c, w.weather_main
FROM traffic_records t
JOIN weather_types w ON t.weather_id = w.weather_id
ORDER BY t.record_time DESC
LIMIT 1;

SELECT record_time, traffic_volume, temp_c
FROM traffic_records
WHERE record_time BETWEEN '2017-06-01 00:00:00' AND '2017-06-01 23:59:59'
ORDER BY record_time;

SELECT HOUR(record_time) AS hour_of_day,
       ROUND(AVG(traffic_volume), 0) AS avg_traffic
FROM traffic_records
GROUP BY HOUR(record_time)
ORDER BY hour_of_day;

SELECT w.weather_main,
       COUNT(*) AS num_hours,
       ROUND(AVG(t.traffic_volume), 0) AS avg_traffic
FROM traffic_records t
JOIN weather_types w ON t.weather_id = w.weather_id
GROUP BY w.weather_main
ORDER BY avg_traffic DESC;

SELECT CASE WHEN t.holiday_id IS NULL THEN 'Normal day (midnight)' ELSE h.holiday_name END AS day_type,
       COUNT(*) AS num_hours,
       ROUND(AVG(t.traffic_volume), 0) AS avg_traffic
FROM traffic_records t
LEFT JOIN holidays h ON t.holiday_id = h.holiday_id
WHERE HOUR(t.record_time) = 0
GROUP BY day_type
ORDER BY avg_traffic;

SELECT YEAR(record_time) AS year,
       COUNT(*) AS hours_recorded,
       ROUND(AVG(traffic_volume), 0) AS avg_traffic
FROM traffic_records
GROUP BY YEAR(record_time)
ORDER BY year;