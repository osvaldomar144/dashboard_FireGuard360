import os
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, window, avg, to_date, lit, when, struct, to_json
from pyspark.sql.types import DoubleType, IntegerType
from pyspark.ml import PipelineModel
from pyspark.ml.feature import VectorAssembler
from pyspark.sql.functions import udf

# ========== Config ==========
CHECKPOINT_URI = os.environ.get("CHECKPOINT_URI", "s3a://lake/checkpoints")
MODEL_PATH = "s3a://lake/models/kmeans_k3"

spark = (
    SparkSession.builder
    .appName("fg360-riskindex-10m")
    .getOrCreate()
)
spark.sparkContext.setLogLevel("WARN")

# Stream dagli aggregati 1m (gold)
agg1m = (
    spark.readStream
    .format("parquet")
    .load("s3a://lake/gold/sensor_stats_1m")
)

# --- Fire Risk Index (per cella, finestra 10 minuti) ---
def clamp01(x):
    return when(x < 0, 0).when(x > 1, 1).otherwise(x)

norm_temp = clamp01((col("avg_temp") - 20) / 25.0)    # 20..45°C
norm_hum  = clamp01(col("avg_hum") / 100.0)           # 0..100%
norm_gas  = clamp01((col("avg_gas") - 200) / 800.0)   # 200..1000
norm_pm25 = clamp01(col("avg_pm25") / 100.0)          # 0..100
norm_wind = clamp01(col("avg_wind") / 15.0)           # 0..15 m/s
firi100_inst = (0.35*norm_temp + 0.30*norm_gas + 0.15*norm_wind + 0.10*norm_pm25 + 0.10*(1.0 - norm_hum)) * 100.0

# Aggregazione 10m per cella
win10 = (
    agg1m
    .withWatermark("ts", "15 minutes")
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

# --- MLlib: aggiungi cluster e distanza se esiste un modello ---
assembler = VectorAssembler(
    inputCols=["avg_temp","avg_hum","avg_gas","avg_pm25","avg_wind"],
    outputCol="features_raw"
)

def attach_kmeans(df):
    try:
        pipeModel = PipelineModel.load(MODEL_PATH)   # scaler + KMeansModel
    except Exception:
        return (
            df.withColumn("cluster", lit(None).cast(IntegerType()))
              .withColumn("distance", lit(None).cast(DoubleType()))
        )

    df2 = assembler.transform(df)
    scored = pipeModel.transform(df2)  # aggiunge "features" (scalate) e "prediction"
    kmm = pipeModel.stages[-1]         # KMeansModel
    centers = [c.toArray().tolist() for c in kmm.clusterCenters()]
    bc_centers = df.sparkSession.sparkContext.broadcast(centers)

    def dist_to_center(features, pred):
        if features is None or pred is None:
            return None
        c = bc_centers.value[int(pred)]
        s = 0.0
        arr = features.toArray()
        for i in range(len(arr)):
            d = arr[i] - c[i]
            s += d * d
        return s ** 0.5

    dist_udf = udf(dist_to_center, DoubleType())
    out = (
        scored
        .withColumn("cluster", col("prediction").cast(IntegerType()))
        .withColumn("distance", dist_udf(col("features"), col("prediction")))
        .drop("features_raw")
    )
    return out

risk10m = attach_kmeans(win10)

# --- Sink: Cassandra ---
(
    risk10m.select("cell_id","bucket_date","window_start","firi","level","cluster","distance")
    .writeStream
    .outputMode("append")  # <== Cassandra supporta solo append
    .format("org.apache.spark.sql.cassandra")
    .option("keyspace", "fg360")
    .option("table", "risk_index_10m")
    .option("checkpointLocation", f"{CHECKPOINT_URI}/risk_index/cassandra")
    .start()
)

# --- Sink: Kafka topic risk.index (JSON) ---
out_k = risk10m.select(
    to_json(struct("cell_id","bucket_date","window_start","firi","level","cluster","distance")).alias("value")
)
(
    out_k.writeStream
    .format("kafka")
    .option("kafka.bootstrap.servers", "kafka:9092")
    .option("topic", "risk.index")
    .option("checkpointLocation", f"{CHECKPOINT_URI}/risk_index/kafka")
    .start()
)

# --- Sink: S3/Parquet (gold) ---
(
    risk10m.writeStream
    .format("parquet")
    .option("path", "s3a://lake/gold/risk_index_10m")
    .option("checkpointLocation", f"{CHECKPOINT_URI}/risk_index/s3")
    .start()
)

spark.streams.awaitAnyTermination()
