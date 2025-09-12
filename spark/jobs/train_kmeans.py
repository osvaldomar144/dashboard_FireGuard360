import os
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, to_date
from pyspark.ml import Pipeline
from pyspark.ml.feature import VectorAssembler, StandardScaler
from pyspark.ml.clustering import KMeans

GOLD_PATH  = os.environ.get("GOLD_PATH",  "s3a://lake/gold/sensor_stats_1m")
MODEL_PATH = os.environ.get("MODEL_PATH", "s3a://lake/models/kmeans_k3")
MIN_DATE   = os.environ.get("MIN_DATE")   # opzionale: "2025-09-01"
MAX_DATE   = os.environ.get("MAX_DATE")

spark = (
    SparkSession.builder
    .appName("fg360-train-kmeans")
    .getOrCreate()
)
spark.sparkContext.setLogLevel("WARN")

df = spark.read.parquet(GOLD_PATH)

# Filtri temporali opzionali (se serve addestrare su un range)
if "bucket_date" in df.columns:
    df = df.withColumn("bucket_date", to_date(col("bucket_date").cast("string")))
    if MIN_DATE: df = df.filter(col("bucket_date") >= MIN_DATE)
    if MAX_DATE: df = df.filter(col("bucket_date") <= MAX_DATE)

df = df.select("avg_temp","avg_hum","avg_gas","avg_pm25","avg_wind").na.drop()

assembler = VectorAssembler(
    inputCols=["avg_temp","avg_hum","avg_gas","avg_pm25","avg_wind"],
    outputCol="features_raw"
)
scaler = StandardScaler(inputCol="features_raw", outputCol="features", withMean=True, withStd=True)
kmeans = KMeans(featuresCol="features", k=3, seed=7, maxIter=50, initSteps=2)

pipe = Pipeline(stages=[assembler, scaler, kmeans])
model = pipe.fit(df)

model.write().overwrite().save(MODEL_PATH)

km = model.stages[-1]
centers = [c.toArray().tolist() for c in km.clusterCenters()]
print("KMeans centers (scaled):", centers)

spark.stop()