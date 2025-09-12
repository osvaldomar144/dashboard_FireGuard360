import os, re
from pyspark.sql import SparkSession
from pyspark.sql.functions import from_json, col, window, avg, max, count, to_date
from pyspark.sql.types import (
    StructType, StructField, TimestampType, StringType, DoubleType, IntegerType
)

# ========== Config ==========
KAFKA_BOOTSTRAP = os.environ.get("KAFKA_BOOTSTRAP", "kafka:9092")
KAFKA_TOPIC     = os.environ.get("RAW_TOPIC") or os.environ.get("KAFKA_TOPIC", "sensors.raw")
STARTING_OFFSETS= os.environ.get("STARTING_OFFSETS", "latest")
CHECKPOINT_URI  = os.environ.get("CHECKPOINT_URI", "s3a://lake/checkpoints")
AGG_WATERMARK   = os.environ.get("AGG1M_WATERMARK") or os.environ.get("AGG_WATERMARK", "2 minutes")
TRIGGER         = os.environ.get("TRIGGER", "5 seconds")

safe_topic = re.sub(r"[^a-zA-Z0-9_.-]", "_", KAFKA_TOPIC)
CHK_ALL   = f"{CHECKPOINT_URI}/agg1m/{safe_topic}"  # <-- unico checkpoint

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
    .appName(f"fg360-agg1m-{safe_topic}")
    # ribadisco conf cassandra per evitare dipendenza esclusiva da spark-defaults
    .config("spark.cassandra.connection.host", "cassandra")
    .config("spark.cassandra.connection.port", "9042")
    .config("spark.cassandra.connection.localDC", "datacenter1")
    .config("spark.cassandra.output.consistency.level", "LOCAL_ONE")
    .getOrCreate()
)
spark.sparkContext.setLogLevel("WARN")

raw = (spark.readStream.format("kafka")
    .option("kafka.bootstrap.servers", KAFKA_BOOTSTRAP)
    .option("subscribe", KAFKA_TOPIC)
    .option("startingOffsets", STARTING_OFFSETS)
    .option("failOnDataLoss", "false")
    .load()
    .selectExpr("CAST(value AS STRING) as json")
    .select(from_json("json", schema).alias("r"))
    .select("r.*")
    .withWatermark("ts", AGG_WATERMARK)
)

clean = raw.filter(
    col("ts").isNotNull() & col("sensor_id").isNotNull() & col("loc.cell_id").isNotNull()
).select(
    col("ts"), col("sensor_id"),
    col("loc.cell_id").alias("cell_id"),
    col("metrics.temp").alias("temp"),
    col("metrics.hum").alias("hum"),
    col("metrics.gas").alias("gas"),
    col("metrics.pm25").alias("pm25"),
    col("metrics.wind").alias("wind")
)

agg1m = (clean.groupBy(window(col("ts"), "1 minute"), col("sensor_id"), col("cell_id"))
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
    .select("cell_id","sensor_id","bucket_date","ts",
            "avg_temp","max_temp","avg_hum","avg_gas","avg_pm25","avg_wind","count")
)

def write_sinks(batch_df, batch_id):
    rows = batch_df.count()
    print(f"[agg1m] batch_id={batch_id} rows={rows}")
    if rows == 0:
        return
    # Cassandra
    to_cass = batch_df.select(
        "sensor_id","bucket_date","ts",
        "avg_temp","max_temp","avg_hum","avg_gas","avg_pm25","avg_wind","count"
    )
    try:
        (to_cass.write
            .format("org.apache.spark.sql.cassandra")
            .mode("append")
            .options(keyspace="fg360", table="sensor_metrics_1m")
            .save())
        print(f"[agg1m] batch_id={batch_id} cassandra OK")
    except Exception as e:
        print(f"[agg1m] batch_id={batch_id} cassandra ERROR: {e}")
        raise

    # Parquet (gold)
    try:
        (batch_df.write
            .mode("append")
            .format("parquet")
            .option("path", "s3a://lake/gold/sensor_stats_1m")
            .save())
        print(f"[agg1m] batch_id={batch_id} parquet OK")
    except Exception as e:
        print(f"[agg1m] batch_id={batch_id} parquet ERROR: {e}")
        raise

(agg1m.writeStream
    .outputMode("append")                         # <--- append per agg + watermark
    .foreachBatch(write_sinks)
    .option("checkpointLocation", CHK_ALL)        # <--- unico checkpoint
    .trigger(processingTime=TRIGGER)
    .start()
)

spark.streams.awaitAnyTermination()
