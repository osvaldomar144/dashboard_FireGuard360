-- Creazione del database
CREATE DATABASE IF NOT EXISTS fireGuard360_db;
USE fireGuard360_db;

-- 1. Tabella per i dati grezzi
CREATE TABLE IF NOT EXISTS sensor_data (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    sensor_id VARCHAR(50) NOT NULL,
    timestamp DATETIME NOT NULL,
    temperature DECIMAL(5,2) NULL,
    humidity DECIMAL(5,2) NULL,
    gas DECIMAL(7,2) NULL,
    INDEX idx_sensor_time (sensor_id, timestamp)
);

-- 2. Tabella aggregati per finestre temporali
CREATE TABLE IF NOT EXISTS sensor_data_analysis (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    sensor_id VARCHAR(50) NOT NULL,
    avg_temperature FLOAT NOT NULL,
    window_start DATETIME NOT NULL,
    window_end DATETIME NOT NULL,
    UNIQUE KEY unique_sensor_window (sensor_id, window_start, window_end),  -- chiave univoca
    INDEX idx_sensor_window (sensor_id, window_start, window_end)
);

-- 3. Tabella per alert incendio (eventi critici)
CREATE TABLE IF NOT EXISTS fire_risk_alerts (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    sensor_id VARCHAR(50) NOT NULL,
    alert_type VARCHAR(100) NOT NULL,
    description TEXT,
    timestamp DATETIME NOT NULL,
    triggered_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_sensor_alert_time (sensor_id, timestamp)
);


-- 4. Tabella per credenziali
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password VARCHAR(100) NOT NULL,
    role ENUM('admin', 'operator') DEFAULT 'operator'
);
