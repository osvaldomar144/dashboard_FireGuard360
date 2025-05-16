from pyspark.sql import SparkSession
from pyspark.sql.functions import from_json, col, window, avg, to_timestamp, lit
from pyspark.sql.types import StructType, StringType, FloatType, TimestampType

# Schema dei dati JSON ricevuti da Kafka
schema = StructType() \
    .add("temperature", FloatType()) \
    .add("humidity", FloatType()) \
    .add("gas", FloatType()) \
    .add("sensor_id", StringType()) \
    .add("timestamp", TimestampType())

# Inizializza Spark
spark = SparkSession.builder \
    .appName("SensorDataProcessor") \
    .master("spark://spark-master:7077") \
    .getOrCreate()

# Legge dal topic Kafka
df_raw = spark.readStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", "kafka:9092") \
    .option("subscribe", "sensordata") \
    .option("startingOffsets", "latest") \
    .load()

# Decodifica il messaggio
df_parsed = df_raw.selectExpr("CAST(value AS STRING)") \
    .select(from_json(col("value"), schema).alias("data")) \
    .select("data.*") \
    .withColumn("timestamp", to_timestamp("timestamp"))

# 1. Scrittura dati grezzi
def write_raw_to_mysql(batch_df, batch_id):
    batch_df.write \
        .format("jdbc") \
        .option("url", "jdbc:mysql://mysql:3306/fireGuard360_db") \
        .option("dbtable", "sensor_data") \
        .option("user", "fireguard_user") \
        .option("password", "fireguard_pass") \
        .option("driver", "com.mysql.cj.jdbc.Driver") \
        .mode("append") \
        .save()

df_parsed.writeStream \
    .foreachBatch(write_raw_to_mysql) \
    .outputMode("append") \
    .option("checkpointLocation", "/tmp/checkpoints/raw") \
    .start()


# 2. Scrittura aggregati
df_avg = df_parsed \
    .withWatermark("timestamp", "2 minutes") \
    .groupBy(
        window(col("timestamp"), "1 minute"),
        col("sensor_id")
    ).agg(avg("temperature").alias("avg_temperature")) \
    .select(
        col("sensor_id"),
        col("avg_temperature"),
        col("window.start").alias("window_start"),
        col("window.end").alias("window_end")
    )


def write_avg_to_mysql(batch_df, batch_id):
    # Rimuove duplicati per (sensor_id, window_start, window_end) e conserva ultimo valore
    deduplicated_df = batch_df.dropDuplicates(["sensor_id", "window_start", "window_end"])

    deduplicated_df.write \
        .format("jdbc") \
        .option("url", "jdbc:mysql://mysql:3306/fireGuard360_db") \
        .option("dbtable", "sensor_data_analysis") \
        .option("user", "fireguard_user") \
        .option("password", "fireguard_pass") \
        .option("driver", "com.mysql.cj.jdbc.Driver") \
        .mode("append") \
        .save()

df_avg.writeStream \
    .foreachBatch(write_avg_to_mysql) \
    .outputMode("update") \
    .option("checkpointLocation", "/tmp/checkpoints/avg") \
    .start()

# 3. Scrittura alert rischio incendio
df_alerts = df_parsed \
    .filter((col("temperature") > 45) & (col("humidity") < 20)) \
    .withColumn("alert_type", lit("High Fire Risk")) \
    .withColumn("description", lit("Temperature > 45°C and Humidity < 20%")) \
    .select(
        col("sensor_id"),
        col("alert_type"),
        col("description"),
        col("timestamp")
    )

def write_alerts_to_mysql(batch_df, batch_id):
    if batch_df.isEmpty():
        return
    batch_df.write \
        .format("jdbc") \
        .option("url", "jdbc:mysql://mysql:3306/fireGuard360_db") \
        .option("dbtable", "fire_risk_alerts") \
        .option("user", "fireguard_user") \
        .option("password", "fireguard_pass") \
        .option("driver", "com.mysql.cj.jdbc.Driver") \
        .mode("append") \
        .save()

df_alerts.writeStream \
    .foreachBatch(write_alerts_to_mysql) \
    .outputMode("append") \
    .option("checkpointLocation", "/tmp/checkpoints/alerts") \
    .start()


# Avvia tutti i flussi
spark.streams.awaitAnyTermination()
