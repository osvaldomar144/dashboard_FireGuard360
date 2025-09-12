# spark/jobs/risk_index.py
import os
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, window, avg, to_date, lit, when, struct, to_json, udf
from pyspark.sql.types import (StructType, StructField, StringType, DateType, TimestampType,
                               DoubleType, LongType, IntegerType)
from pyspark.ml import PipelineModel
from pyspark.ml.feature import VectorAssembler

# ========== Config ==========
CHECKPOINT_URI = os.environ.get("CHECKPOINT_URI", "s3a://lake/checkpoints")
MODEL_PATH     = os.environ.get("MODEL_PATH", "s3a://lake/models/kmeans_k3")
RISK_WATERMARK = os.environ.get("RISK_WATERMARK", "15 minutes")
TRIGGER        = os.environ.get("TRIGGER", "10 seconds")
INPUT_PATH     = os.environ.get("INPUT_PATH", "s3a://lake/gold/sensor_stats_1m")
KAFKA_BOOTSTRAP= os.environ.get("KAFKA_BOOTSTRAP", "kafka:9092")

aggSchema = StructType([
    StructField("cell_id",     StringType(),   True),
    StructField("sensor_id",   StringType(),   True),
    StructField("bucket_date", DateType(),     True),
    StructField("ts",          TimestampType(),True),
    StructField("avg_temp",    DoubleType(),   True),
    StructField("max_temp",    DoubleType(),   True),
    StructField("avg_hum",     DoubleType(),   True),
    StructField("avg_gas",     DoubleType(),   True),
    StructField("avg_pm25",    DoubleType(),   True),
    StructField("avg_wind",    DoubleType(),   True),
    StructField("count",       LongType(),     False),
])

spark = (
    SparkSession.builder
    .appName("fg360-riskindex-10m")
    # Conf Cassandra esplicite (evita silenzi se spark-defaults non viene letto)
    .config("spark.cassandra.connection.host", "cassandra")
    .config("spark.cassandra.connection.port", "9042")
    .config("spark.cassandra.connection.localDC", "datacenter1")
    .config("spark.cassandra.output.consistency.level", "LOCAL_ONE")
    .getOrCreate()
)
spark.sparkContext.setLogLevel("WARN")

# === Source ===
agg1m = (
    spark.readStream
         .format("parquet")
         .schema(aggSchema)
         .load(INPUT_PATH)
)

# --- FIRI ---
def clamp01(x):
    return when(x < 0, 0).when(x > 1, 1).otherwise(x)

norm_temp = clamp01((col("avg_temp") - 20) / 25.0)
norm_hum  = clamp01(col("avg_hum") / 100.0)
norm_gas  = clamp01((col("avg_gas") - 200) / 800.0)
norm_pm25 = clamp01(col("avg_pm25") / 100.0)
norm_wind = clamp01(col("avg_wind") / 15.0)
firi100_inst = (0.35*norm_temp + 0.30*norm_gas + 0.15*norm_wind + 0.10*norm_pm25 + 0.10*(1.0 - norm_hum)) * 100.0

win10 = (
    agg1m
    .withWatermark("ts", RISK_WATERMARK)
    .groupBy(window(col("ts"), "10 minutes"), col("cell_id"))
    .agg(
        avg("avg_temp").alias("avg_temp"),
        avg("avg_hum").alias("avg_hum"),
        avg("avg_gas").alias("avg_gas"),
        avg("avg_pm25").alias("avg_pm25"),
        avg("avg_wind").alias("avg_wind"),
        avg(firi100_inst).alias("firi")
    )
    .withColumn("level", when(col("firi") < 33, "LOW").when(col("firi") < 66, "MED").otherwise("HIGH"))
    .withColumn("window_start", col("window.start"))
    .withColumn("bucket_date", to_date(col("window.start")))
    .select("cell_id","bucket_date","window_start","avg_temp","avg_hum","avg_gas","avg_pm25","avg_wind","firi","level")
)

# --- MLlib opzionale ---
assembler = VectorAssembler(
    inputCols=["avg_temp","avg_hum","avg_gas","avg_pm25","avg_wind"],
    outputCol="features_raw"
)

def attach_kmeans(df):
    try:
        pipeModel = PipelineModel.load(MODEL_PATH)
    except Exception:
        return df.withColumn("cluster", lit(None).cast(IntegerType())) \
                 .withColumn("distance", lit(None).cast(DoubleType()))

    df2 = assembler.transform(df)
    scored = pipeModel.transform(df2)
    kmm = pipeModel.stages[-1]
    centers = [c.toArray().tolist() for c in kmm.clusterCenters()]
    bc_centers = df.sparkSession.sparkContext.broadcast(centers)

    def dist_to_center(features, pred):
        if features is None or pred is None:
            return None
        c = bc_centers.value[int(pred)]
        arr = features.toArray()
        s = 0.0
        for i in range(len(arr)):
            d = arr[i] - c[i]
            s += d * d
        return s ** 0.5

    dist_udf = udf(dist_to_center, DoubleType())
    return (scored
            .withColumn("cluster", col("prediction").cast(IntegerType()))
            .withColumn("distance", dist_udf(col("features"), col("prediction")))
            .drop("features_raw"))

risk10m = attach_kmeans(win10)

# --- Sinks ---
def write_sinks(batch_df, batch_id):
    rows = batch_df.count()
    print(f"[risk] batch_id={batch_id} rows={rows}")
    if rows == 0:
        return

    # Cassandra
    try:
        (batch_df.select("cell_id","bucket_date","window_start","firi","level","cluster","distance")
         .write
         .format("org.apache.spark.sql.cassandra")
         .mode("append")   # <<<< append
         .options(keyspace="fg360", table="risk_index_10m")
         .save())
        print(f"[risk] cassandra OK")
    except Exception as e:
        print(f"[risk] cassandra ERROR: {e}")
        raise

    # Parquet gold
    try:
        (batch_df.write
         .mode("append")
         .format("parquet")
         .option("path", "s3a://lake/gold/risk_index_10m")
         .save())
        print(f"[risk] parquet OK")
    except Exception as e:
        print(f"[risk] parquet ERROR: {e}")
        raise

(risk10m.writeStream
    .outputMode("append")  # <<<< non 'update'
    .foreachBatch(write_sinks)
    .option("checkpointLocation", f"{CHECKPOINT_URI}/risk_index/v2")  # nuova path per evitare vecchi checkpoint
    .trigger(processingTime=TRIGGER)
    .start())

# Kafka (sink separato)
out_k = risk10m.select(
    to_json(struct("cell_id","bucket_date","window_start","firi","level","cluster","distance")).alias("value")
)
(out_k.writeStream
    .format("kafka")
    .option("kafka.bootstrap.servers", KAFKA_BOOTSTRAP)
    .option("topic", "risk.index")
    .option("checkpointLocation", f"{CHECKPOINT_URI}/risk_index_kafka/v2")  # checkpoint separato
    .trigger(processingTime=TRIGGER)
    .start())

spark.streams.awaitAnyTermination()
