-- Task 2: MySQL schema for the hourly traffic dataset

CREATE DATABASE IF NOT EXISTS traffic_db;
USE traffic_db;

DROP TABLE IF EXISTS traffic_records;
DROP TABLE IF EXISTS weather_types;
DROP TABLE IF EXISTS holidays;

-- every weather_main + weather_description pair that shows up in the data
CREATE TABLE weather_types (
    weather_id          INT AUTO_INCREMENT PRIMARY KEY,
    weather_main        VARCHAR(30)  NOT NULL,
    weather_description VARCHAR(60)  NOT NULL,
    UNIQUE KEY uq_weather (weather_main, weather_description)
);

-- holiday names (only a handful of them)
CREATE TABLE holidays (
    holiday_id   INT AUTO_INCREMENT PRIMARY KEY,
    holiday_name VARCHAR(50) NOT NULL UNIQUE
);

-- one row per hour
CREATE TABLE traffic_records (
    record_id      INT AUTO_INCREMENT PRIMARY KEY,
    record_time    DATETIME NOT NULL UNIQUE,   -- the timestamp, unique so no duplicate hours
    traffic_volume INT      NOT NULL,          -- target variable
    temp_c         DECIMAL(5,2) NULL,
    rain_1h        DECIMAL(7,2) NULL,
    snow_1h        DECIMAL(5,2) NULL,
    clouds_all     INT NULL,
    weather_id     INT NOT NULL,
    holiday_id     INT NULL,                   -- NULL means not a holiday
    FOREIGN KEY (weather_id) REFERENCES weather_types(weather_id),
    FOREIGN KEY (holiday_id) REFERENCES holidays(holiday_id)
);

CREATE INDEX idx_traffic_weather ON traffic_records(weather_id);