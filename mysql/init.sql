-- Creazione del database
CREATE DATABASE IF NOT EXISTS fireGuard360_db;
USE fireGuard360_db;

-- ========================================================================================
--                                  TABELLE PRINCIPALI
-- ========================================================================================

-- =========================================
-- 1. METADATA SENSORI
-- =========================================
CREATE TABLE IF NOT EXISTS sensors (
    id VARCHAR(50) PRIMARY KEY,
    description VARCHAR(100),
    location VARCHAR(100),
    latitude DECIMAL(9,6),
    longitude DECIMAL(9,6),
    installed_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- =========================================
-- 2. FIRE RISK ALERTS
-- =========================================
CREATE TABLE IF NOT EXISTS fire_risk_alerts (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    sensor_id VARCHAR(50) NOT NULL,
    alert_type VARCHAR(100) NOT NULL,
    description TEXT,
    severity ENUM('low', 'moderate', 'high', 'critical') NOT NULL,
    timestamp DATETIME NOT NULL,
    triggered_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_sensor_alert_time (sensor_id, timestamp)
);

-- =========================================
-- 3. SENSOR STATS (Aggregati)
-- =========================================

CREATE TABLE IF NOT EXISTS sensor_stats (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    sensor_id VARCHAR(50) NOT NULL,
    window_start DATETIME NOT NULL,
    window_end DATETIME NOT NULL,
    avg_temperature FLOAT,
    avg_humidity FLOAT,
    avg_gas FLOAT,
    max_temperature FLOAT,
    max_gas FLOAT,
    UNIQUE KEY unique_sensor_window (sensor_id, window_start, window_end),
    INDEX idx_sensor_window (sensor_id, window_start)
);

-- Tabella di STAGING per Spark
CREATE TABLE IF NOT EXISTS sensor_stats_staging (
    sensor_id VARCHAR(50) NOT NULL,
    window_start DATETIME NOT NULL,
    window_end DATETIME NOT NULL,
    avg_temperature FLOAT,
    avg_humidity FLOAT,
    avg_gas FLOAT,
    max_temperature FLOAT,
    max_gas FLOAT
);

-- Stored Procedure per upsert
DROP PROCEDURE IF EXISTS upsert_stats;
DELIMITER //

CREATE PROCEDURE upsert_stats()
BEGIN
    INSERT INTO sensor_stats (
        sensor_id, window_start, window_end,
        avg_temperature, avg_humidity, avg_gas,
        max_temperature, max_gas
    )
    SELECT
        sensor_id, window_start, window_end,
        avg_temperature, avg_humidity, avg_gas,
        max_temperature, max_gas
    FROM sensor_stats_staging
    ON DUPLICATE KEY UPDATE
        avg_temperature = VALUES(avg_temperature),
        avg_humidity = VALUES(avg_humidity),
        avg_gas = VALUES(avg_gas),
        max_temperature = VALUES(max_temperature),
        max_gas = VALUES(max_gas);

    TRUNCATE TABLE sensor_stats_staging;
END //

DELIMITER ;

-- =========================================
-- 4. FIRE RISK INDEX
-- =========================================

CREATE TABLE IF NOT EXISTS fire_risk_index (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    sensor_id VARCHAR(50) NOT NULL,
    risk_score FLOAT NOT NULL,
    risk_level ENUM('low', 'moderate', 'high', 'critical') NOT NULL,
    calculated_at DATETIME NOT NULL,
    INDEX idx_sensor_risk (sensor_id, calculated_at)
);

-- Staging per risk index
CREATE TABLE IF NOT EXISTS fire_risk_index_staging (
    sensor_id VARCHAR(50) NOT NULL,
    risk_score FLOAT NOT NULL,
    risk_level ENUM('low', 'moderate', 'high', 'critical') NOT NULL,
    calculated_at DATETIME NOT NULL
);

-- Stored Procedure per upsert del rischio
DROP PROCEDURE IF EXISTS upsert_risk_index;
DELIMITER //

CREATE PROCEDURE upsert_risk_index()
BEGIN
    INSERT INTO fire_risk_index (
        sensor_id, risk_score, risk_level, calculated_at
    )
    SELECT
        sensor_id, risk_score, risk_level, calculated_at
    FROM fire_risk_index_staging
    ON DUPLICATE KEY UPDATE
        risk_score = VALUES(risk_score),
        risk_level = VALUES(risk_level),
        calculated_at = VALUES(calculated_at);

    TRUNCATE TABLE fire_risk_index_staging;
END //

DELIMITER ;

-- =========================================
-- 5. UTENTI
-- =========================================
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password VARCHAR(100) NOT NULL,
    role ENUM('admin', 'operator') DEFAULT 'operator'
);

-- ========================================================================================
-- 6. DATI GREZZI SENSORI (RAW)
-- ========================================================================================

-- Tabella dati grezzi con campo danger_value
CREATE TABLE IF NOT EXISTS raw_sensor_data (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    sensor_id VARCHAR(50) NOT NULL,
    temperature FLOAT,
    humidity FLOAT,
    gas FLOAT,
    danger_value FLOAT, -- calcolato o derivato
    detected_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_sensor_time (sensor_id, detected_at)
);

-- Tabella di STAGING per Spark (senza ID auto-incrementale)
CREATE TABLE IF NOT EXISTS raw_sensor_data_staging (
    sensor_id VARCHAR(50) NOT NULL,
    temperature FLOAT,
    humidity FLOAT,
    gas FLOAT,
    danger_value FLOAT,
    detected_at DATETIME NOT NULL
);

-- Stored Procedure per upsert (append raw data)
DROP PROCEDURE IF EXISTS insert_raw_sensor_data;
DELIMITER //

CREATE PROCEDURE insert_raw_sensor_data()
BEGIN
    INSERT INTO raw_sensor_data (
        sensor_id, temperature, humidity, gas, danger_value, detected_at
    )
    SELECT
        sensor_id, temperature, humidity, gas, danger_value, detected_at
    FROM raw_sensor_data_staging;

    TRUNCATE TABLE raw_sensor_data_staging;
END //

DELIMITER ;

-- =========================================
-- 7. DANGER LEVEL AGGREGATO DI SISTEMA
-- =========================================

-- Tabella principale
CREATE TABLE IF NOT EXISTS system_danger_level (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    avg_danger FLOAT,
    max_danger FLOAT,
    danger_level INT, -- 0: nessun rischio, 1: potenziale, 2: confermato
    calculated_at DATETIME NOT NULL,
    INDEX idx_danger_time (calculated_at)
);

ALTER TABLE system_danger_level
ADD CONSTRAINT uc_calculated_at UNIQUE (calculated_at);

-- Tabella di staging per Spark
CREATE TABLE IF NOT EXISTS system_danger_level_staging (
    avg_danger FLOAT,
    max_danger FLOAT,
    danger_level INT,
    calculated_at DATETIME NOT NULL
);

-- Stored Procedure per upsert del danger level aggregato
DROP PROCEDURE IF EXISTS upsert_system_danger_level;
DELIMITER //

CREATE PROCEDURE upsert_system_danger_level()
BEGIN
    INSERT INTO system_danger_level (
        avg_danger, max_danger, danger_level, calculated_at
    )
    SELECT
        avg_danger, max_danger, danger_level, calculated_at
    FROM system_danger_level_staging
    ON DUPLICATE KEY UPDATE
        avg_danger = VALUES(avg_danger),
        max_danger = VALUES(max_danger),
        danger_level = VALUES(danger_level);

    TRUNCATE TABLE system_danger_level_staging;
END //

DELIMITER ;


-- ========================================================================================
--                          ALL STORED PROCEDURES
-- ========================================================================================

-- Stored procedure per ottenere gli ultimi N record dalla tabella fire_risk_alerts
DROP PROCEDURE IF EXISTS get_latest_fire_alerts;

DELIMITER //

CREATE PROCEDURE get_latest_fire_alerts(IN limit_rows INT)
BEGIN
    SELECT *
    FROM fire_risk_alerts
    ORDER BY timestamp DESC
    LIMIT limit_rows;
END //

DELIMITER ;

-- Ultimi alert per sensore
DROP PROCEDURE IF EXISTS get_alerts_by_sensor;
DELIMITER //

CREATE PROCEDURE get_alerts_by_sensor(
    IN sensor_id_param VARCHAR(50),
    IN limit_rows INT,
    IN start_date DATETIME,
    IN end_date DATETIME
)
BEGIN
    SELECT *
    FROM fire_risk_alerts
    WHERE sensor_id = sensor_id_param
      AND timestamp BETWEEN IFNULL(start_date, CURDATE()) AND IFNULL(end_date, NOW())
    ORDER BY timestamp DESC
    LIMIT limit_rows;
END //

DELIMITER ;

-- Conteggio alert per severità
DROP PROCEDURE IF EXISTS count_alerts_by_severity;
DELIMITER //

CREATE PROCEDURE count_alerts_by_severity(
    IN start_date DATETIME,
    IN end_date DATETIME
)
BEGIN
    SELECT severity, COUNT(*) AS total_alerts
    FROM fire_risk_alerts
    WHERE timestamp BETWEEN IFNULL(start_date, CURDATE()) AND IFNULL(end_date, NOW())
    GROUP BY severity
    ORDER BY FIELD(severity, 'critical', 'high', 'moderate', 'low');
END //

DELIMITER ;

-- Ultime medie aggregate per sensore TOCHECK
DROP PROCEDURE IF EXISTS get_latest_sensor_stats;
DELIMITER //

CREATE PROCEDURE get_latest_sensor_stats(
    IN sensor_id_param VARCHAR(50),
    IN limit_rows INT,
    IN start_date DATETIME,
    IN end_date DATETIME
)
BEGIN
    SELECT *
    FROM sensor_stats
    WHERE sensor_id = sensor_id_param
      AND window_end BETWEEN IFNULL(start_date, CURDATE()) AND IFNULL(end_date, NOW())
    ORDER BY window_end DESC
    LIMIT limit_rows;
END //

DELIMITER ;

-- Ultimo record di stats per ciascun sensore (senza parametri)
DROP PROCEDURE IF EXISTS get_latest_stats_per_sensor;
DELIMITER //

CREATE PROCEDURE get_latest_stats_per_sensor()
BEGIN
    SELECT s.*
    FROM sensor_stats s
    INNER JOIN (
        SELECT sensor_id, MAX(window_end) AS latest_window
        FROM sensor_stats
        GROUP BY sensor_id
    ) latest
    ON s.sensor_id = latest.sensor_id AND s.window_end = latest.latest_window;
END //

DELIMITER ;



-- Storico indice di rischio per sensore
DROP PROCEDURE IF EXISTS get_risk_index_history;
DELIMITER //

CREATE PROCEDURE get_risk_index_history(
    IN sensor_id_param VARCHAR(50),
    IN limit_rows INT,
    IN start_date DATETIME,
    IN end_date DATETIME
)
BEGIN
    SELECT *
    FROM fire_risk_index
    WHERE sensor_id = sensor_id_param
      AND calculated_at BETWEEN IFNULL(start_date, CURDATE()) AND IFNULL(end_date, NOW())
    ORDER BY calculated_at DESC
    LIMIT limit_rows;
END //

DELIMITER ;

-- Mappa dei sensori attivi con ultime coordinate
DROP PROCEDURE IF EXISTS get_all_sensor_locations;
DELIMITER //

CREATE PROCEDURE get_all_sensor_locations()
BEGIN
    SELECT id AS sensor_id, description, location, latitude, longitude
    FROM sensors;
END //

DELIMITER ;

-- Ultimo stato rischio per tutti i sensori
DROP PROCEDURE IF EXISTS get_latest_risk_per_sensor;
DELIMITER //

CREATE PROCEDURE get_latest_risk_per_sensor()
BEGIN
    SELECT r1.*
    FROM fire_risk_index r1
    INNER JOIN (
        SELECT sensor_id, MAX(calculated_at) AS latest
        FROM fire_risk_index
        GROUP BY sensor_id
    ) r2 ON r1.sensor_id = r2.sensor_id AND r1.calculated_at = r2.latest;
END //

DELIMITER ;

-- Ultimo alert per ciascun sensore
DROP PROCEDURE IF EXISTS get_last_alert_per_sensor;
DELIMITER //

CREATE PROCEDURE get_last_alert_per_sensor()
BEGIN
    SELECT a.*
    FROM fire_risk_alerts a
    INNER JOIN (
        SELECT sensor_id, MAX(timestamp) AS last_alert_time
        FROM fire_risk_alerts
        GROUP BY sensor_id
    ) latest ON a.sensor_id = latest.sensor_id AND a.timestamp = latest.last_alert_time;
END //

DELIMITER ;


-- Recupera utenti filtrando per ruolo
DROP PROCEDURE IF EXISTS get_users_by_role;
DELIMITER //

CREATE PROCEDURE get_users_by_role(IN user_role ENUM('ADMIN', 'OPERATOR'))
BEGIN
    SELECT 
        id,
        username,
        role
    FROM users
    WHERE role = user_role
    ORDER BY username ASC;
END //

DELIMITER ;

-- Recupera un singolo utente per ID
DROP PROCEDURE IF EXISTS get_user_by_id;
DELIMITER //

CREATE PROCEDURE get_user_by_id(IN user_id INT)
BEGIN
    SELECT 
        id,
        username,
        role
    FROM users
    WHERE id = user_id;
END //

DELIMITER ;

-- ========================================================================================
-- Stored Procedure per ottenere i dati grezzi
-- ========================================================================================
DROP PROCEDURE IF EXISTS get_raw_sensor_data;
DELIMITER //

CREATE PROCEDURE get_raw_sensor_data(
    IN sensor_id_param VARCHAR(50),
    IN start_date DATETIME,
    IN end_date DATETIME
)
BEGIN
    SELECT *
    FROM raw_sensor_data
    WHERE 
        (sensor_id_param IS NULL OR sensor_id = sensor_id_param)
        AND detected_at BETWEEN 
            IFNULL(start_date, CURDATE()) 
            AND 
            IFNULL(end_date, DATE_ADD(CURDATE(), INTERVAL 1 DAY))
    ORDER BY detected_at DESC;
END //

DELIMITER ;

-- Recupera ultimi danger level globali (aggregato di sistema)
DROP PROCEDURE IF EXISTS get_latest_system_danger;
DELIMITER //

CREATE PROCEDURE get_latest_system_danger(
    IN limit_rows INT
)
BEGIN
    SELECT *
    FROM system_danger_level
    ORDER BY calculated_at DESC
    LIMIT limit_rows;
END //

DELIMITER ;