# spark/jobs/batch_offline_daily.py
import os
from datetime import datetime, timedelta
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, avg, max as smax, sum as ssum, to_date, expr, when, lit

GOLD_BASE     = os.getenv("GOLD_BASE", "s3a://lake/gold")
OUT_BASE      = os.getenv("OUT_BASE",  "s3a://lake/gold/daily")
START_DATE    = os.getenv("START_DATE")          # "YYYY-MM-DD"
END_DATE      = os.getenv("END_DATE")
LOOKBACK_DAYS = int(os.getenv("LOOKBACK_DAYS", "3"))

if not START_DATE or not END_DATE:
    today = datetime.utcnow().date()
    end_d = today
    start_d = today - timedelta(days=LOOKBACK_DAYS)
    START_DATE = START_DATE or start_d.strftime("%F")
    END_DATE   = END_DATE   or end_d.strftime("%F")

spark = (SparkSession.builder
         .appName("fg360-batch-offline-daily")
         # conf S3/Cassandra prese da spark-defaults; ribadisco solo Cassandra per coerenza
         .config("spark.cassandra.connection.host", "cassandra")
         .config("spark.cassandra.connection.port", "9042")
         .config("spark.cassandra.connection.localDC", "datacenter1")
         .getOrCreate())
spark.sparkContext.setLogLevel("WARN")

spark.conf.set("spark.sql.sources.partitionOverwriteMode", "dynamic")

def between_dates(df, date_col="bucket_date"):
    return df.filter((col(date_col) >= lit(START_DATE)) & (col(date_col) <= lit(END_DATE)))

print(f"[batch] range: {START_DATE} .. {END_DATE}")

# 1) SENSOR DAILY PER CELLA
s1m = spark.read.parquet(f"{GOLD_BASE}/sensor_stats_1m")
if dict(s1m.dtypes).get("bucket_date") != "date":
    s1m = s1m.withColumn("bucket_date", to_date(col("bucket_date")))
s1m = between_dates(s1m, "bucket_date")

sensor_daily_cell = (s1m.groupBy("bucket_date", "cell_id")
    .agg(
        avg("avg_temp").alias("avg_temp"),
        smax("max_temp").alias("max_temp"),
        avg("avg_hum").alias("avg_hum"),
        avg("avg_gas").alias("avg_gas"),
        avg("avg_pm25").alias("avg_pm25"),
        avg("avg_wind").alias("avg_wind"),
        ssum("count").cast("long").alias("events")
    ))

# meno file: max(1, num_giorni)
repart_target = max(1, len(set([START_DATE, END_DATE])))
(sensor_daily_cell
    .repartition("bucket_date")
    .write.mode("overwrite")
    .partitionBy("bucket_date")
    .parquet(f"{OUT_BASE}/sensor_by_cell"))

# 2) RISK DAILY PER CELLA
r10m = spark.read.parquet(f"{GOLD_BASE}/risk_index_10m")
if dict(r10m.dtypes).get("bucket_date") != "date":
    r10m = r10m.withColumn("bucket_date", to_date(col("bucket_date")))
r10m = between_dates(r10m, "bucket_date")

risk_daily_cell = (r10m.groupBy("bucket_date", "cell_id")
    .agg(
        avg("firi").alias("firi_avg"),
        expr("percentile_approx(firi, 0.95)").alias("firi_p95"),
        ssum(when(col("level") == "HIGH", 1).otherwise(0)).cast("int").alias("high_cnt"),
        ssum(when(col("level") == "MED",  1).otherwise(0)).cast("int").alias("med_cnt"),
        ssum(when(col("level") == "LOW",  1).otherwise(0)).cast("int").alias("low_cnt")
    )
    .withColumn(
        "level_max",
        when(col("high_cnt") > 0, lit("HIGH"))
        .when(col("med_cnt") > 0, lit("MED"))
        .otherwise(lit("LOW"))
    ))

(risk_daily_cell
    .repartition("bucket_date")
    .write.mode("overwrite")
    .partitionBy("bucket_date")
    .parquet(f"{OUT_BASE}/risk_by_cell"))

spark.stop()
