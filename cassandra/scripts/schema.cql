CREATE KEYSPACE IF NOT EXISTS fg360
WITH replication = {'class': 'SimpleStrategy', 'replication_factor': 1};

DROP TABLE IF EXISTS fg360.sensor_metrics_1m;

-- Serie temporali per aggregazioni 1 minuto
CREATE TABLE IF NOT EXISTS fg360.sensor_metrics_1m (
  sensor_id   text,
  bucket_date date,
  ts          timestamp,
  avg_temp    double,
  max_temp    double,
  avg_hum     double,
  avg_gas     double,
  avg_pm25    double,
  avg_wind    double,
  count       bigint,
  PRIMARY KEY ((sensor_id, bucket_date), ts)
);


DROP TABLE IF EXISTS fg360.risk_index_10m;

-- Indice di rischio su finestre da 10 minuti
CREATE TABLE IF NOT EXISTS fg360.risk_index_10m (
  cell_id      text,
  bucket_date  date,
  window_start timestamp,
  firi         double,
  level        text,
  cluster      int,
  distance     double,
  PRIMARY KEY ((cell_id, bucket_date), window_start)
);