-- Creazione del database
CREATE DATABASE IF NOT EXISTS fireGuard360_db;
USE fireGuard360_db;


-- Tabella iniziale per test ---
CREATE TABLE IF NOT EXISTS sensor_data_analysis (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    sensor_id VARCHAR(50) NOT NULL,
    avg_temperature FLOAT NOT NULL,
    window_start DATETIME NOT NULL,
    window_end DATETIME NOT NULL,
    INDEX idx_sensor_window (sensor_id, window_start, window_end)
);

-- Tabella per i dati grezzi dai sensori
CREATE TABLE IF NOT EXISTS sensor_data (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    sensor_id VARCHAR(50) NOT NULL,
    timestamp DATETIME NOT NULL,
    temperature DECIMAL(5,2) NULL,
    humidity DECIMAL(5,2) NULL,
    pressure DECIMAL(7,2) NULL,
    -- aggiungi altri campi sensore se servono
    INDEX idx_sensor_time (sensor_id, timestamp)
);

-- Tabella per i risultati delle analisi in real-time
CREATE TABLE IF NOT EXISTS realtime_analysis (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    sensor_data_id BIGINT NOT NULL,
    anomaly_detected BOOLEAN DEFAULT FALSE,
    anomaly_score DECIMAL(5,2),
    processed_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (sensor_data_id) REFERENCES sensor_data(id) ON DELETE CASCADE,
    INDEX idx_processed_at (processed_at)
);

-- Tabella per risultati delle analisi batch / predittive
CREATE TABLE IF NOT EXISTS batch_analysis (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    sensor_id VARCHAR(50) NOT NULL,
    analysis_time DATETIME NOT NULL,
    predicted_value DECIMAL(7,2),
    confidence_score DECIMAL(5,2),
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_sensor_analysis_time (sensor_id, analysis_time)
);
