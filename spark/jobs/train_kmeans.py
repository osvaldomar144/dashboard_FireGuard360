from pyspark.sql import SparkSession
from pyspark.sql.functions import col
from pyspark.ml import Pipeline
from pyspark.ml.feature import VectorAssembler, StandardScaler
from pyspark.ml.clustering import KMeans

GOLD_PATH  = "s3a://lake/gold/sensor_stats_1m"
MODEL_PATH = "s3a://lake/models/kmeans_k3"

spark = (
    SparkSession.builder
    .appName("fg360-train-kmeans")
    .getOrCreate()
)
spark.sparkContext.setLogLevel("WARN")

# Carica feature dai Parquet gold (minimo necessario)
df = (
    spark.read.parquet(GOLD_PATH)
    .select("avg_temp", "avg_hum", "avg_gas", "avg_pm25", "avg_wind")
    .na.drop()
)

# Pipeline: assembler -> scaler -> KMeans(k=3)
assembler = VectorAssembler(
    inputCols=["avg_temp", "avg_hum", "avg_gas", "avg_pm25", "avg_wind"],
    outputCol="features_raw"
)
scaler = StandardScaler(inputCol="features_raw", outputCol="features", withMean=True, withStd=True)
kmeans = KMeans(featuresCol="features", k=3, seed=7, maxIter=50, initSteps=2)

pipe = Pipeline(stages=[assembler, scaler, kmeans])
model = pipe.fit(df)

# Salva modello (pipeline completa)
model.write().overwrite().save(MODEL_PATH)

# (facoltativo) Stampa i centroidi standardizzati
km = model.stages[-1]
centers = [c.toArray().tolist() for c in km.clusterCenters()]
print("KMeans centers (scaled):", centers)

spark.stop()
