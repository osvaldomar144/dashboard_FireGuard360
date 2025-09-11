import os
from pyspark.sql import SparkSession
from pyspark.sql.functions import from_json, col, window, avg, max, count, to_date
from pyspark.sql.types import (
    StructType, StructField, TimestampType, StringType, DoubleType, IntegerType
)

# ========== Config ==========
CHECKPOINT_URI = os.environ.get("CHECKPOINT_URI", "s3a://lake/checkpoints")

# Schema eventi raw
schema = StructType([
    StructField("ts", TimestampType(), True),
    StructField("sensor_id", StringType(), True),
    StructField("loc", StructType([
        StructField("lat", DoubleType(), True),
        StructField("lon", DoubleType(), True),
        StructField("cell_id", StringType(), True)
    ]), True),
    StructField("metrics", StructType([
        StructField("temp", DoubleType(), True),
        StructField("hum", DoubleType(), True),
        StructField("gas", DoubleType(), True),
        StructField("pm25", DoubleType(), True),
        StructField("wind", DoubleType(), True),
    ]), True),
    StructField("battery", IntegerType(), True)
])

spark = (
    SparkSession.builder
    .appName("fg360-agg1m")
    .getOrCreate()
)
spark.sparkContext.setLogLevel("WARN")

# Ingest Kafka
raw = (
    spark.readStream.format("kafka")
    .option("kafka.bootstrap.servers", "kafka:9092")
    .option("subscribe", "sensors.raw")
    .option("startingOffsets", "latest")
    .load()
    .selectExpr("CAST(value AS STRING) as json")
    .select(from_json("json", schema).alias("r"))
    .select("r.*")
    .withWatermark("ts", "2 minutes")
)

# Clean minimo
clean = raw.filter(
    col("ts").isNotNull() &
    col("sensor_id").isNotNull() &
    col("loc.cell_id").isNotNull()
).select(
    col("ts"),
    col("sensor_id"),
    col("loc.cell_id").alias("cell_id"),
    col("metrics.temp").alias("temp"),
    col("metrics.hum").alias("hum"),
    col("metrics.gas").alias("gas"),
    col("metrics.pm25").alias("pm25"),
    col("metrics.wind").alias("wind")
)

# Agg 1 minuto (per sensore e cella)
agg1m = (
    clean.groupBy(window(col("ts"), "1 minute"), col("sensor_id"), col("cell_id"))
    .agg(
        avg("temp").alias("avg_temp"),
        max("temp").alias("max_temp"),
        avg("hum").alias("avg_hum"),
        avg("gas").alias("avg_gas"),
        avg("pm25").alias("avg_pm25"),
        avg("wind").alias("avg_wind"),
        count("*").alias("count")
    )
    .withColumn("ts", col("window.start"))
    .withColumn("bucket_date", to_date(col("ts")))
    .select(
        "cell_id","sensor_id","bucket_date","ts",
        "avg_temp","max_temp","avg_hum","avg_gas","avg_pm25","avg_wind","count"
    )
)

# Sink 1: Cassandra (serving) - tabella sensor_metrics_1m (senza cell_id)
to_cass = agg1m.select(
    "sensor_id","bucket_date","ts","avg_temp","max_temp","avg_hum","avg_gas","avg_pm25","avg_wind","count"
)
(
    to_cass.writeStream
    .outputMode("append")  # <== Cassandra supporta solo append
    .format("org.apache.spark.sql.cassandra")
    .option("keyspace", "fg360")
    .option("table", "sensor_metrics_1m")
    .option("checkpointLocation", f"{CHECKPOINT_URI}/agg1m/cassandra")
    .start()
)

# Sink 2: S3 Parquet (gold) - mantiene anche cell_id
(
    agg1m.writeStream
    .format("parquet")
    .option("path", "s3a://lake/gold/sensor_stats_1m")
    .option("checkpointLocation", f"{CHECKPOINT_URI}/agg1m/s3")
    .start()
)

spark.streams.awaitAnyTermination()
