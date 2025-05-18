from pyspark.sql import SparkSession
from pyspark.sql.functions import from_json, col, window, avg, to_timestamp, lit
from pyspark.sql.types import StructType, StringType, FloatType, TimestampType
from dotenv import load_dotenv
import os

load_dotenv(dotenv_path="CONFIG_FIREGUARD360.env")

# variabili configurazione per DB
DB_URL = os.getenv("DB_URL")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_DRIVER = os.getenv("DB_DRIVER")
TABLE_RAW_DATA = os.getenv("TABLE_RAW_DATA")
TABLE_AGGREGATED_DATA = os.getenv("TABLE_AGGREGATED_DATA")
TABLE_AGG_STAGING = os.getenv("TABLE_AGG_STAGING")
TABLE_RISK_HISTORY = os.getenv("TABLE_RISK_HISTORY")

# variabili di configurazione per KAFKA
KAFKA_SERVER = os.getenv("KAFKA_SERVER")
KAFKA_TOPIC = os.getenv("KAFKA_TOPIC")

# variabili di configurazione per SPARK
SPARK_APP_NAME = os.getenv("SPARK_APP_NAME")
SPARK_MASTER_URL = os.getenv("SPARK_MASTER_URL")


# Schema dei dati JSON ricevuti da Kafka
schema = StructType() \
    .add("temperature", FloatType()) \
    .add("humidity", FloatType()) \
    .add("gas", FloatType()) \
    .add("sensor_id", StringType()) \
    .add("timestamp", TimestampType())

# Inizializza Spark
spark = SparkSession.builder \
    .appName(SPARK_APP_NAME) \
    .master(SPARK_MASTER_URL) \
    .getOrCreate()

# Legge dal topic Kafka
df_raw = spark.readStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", KAFKA_SERVER) \
    .option("subscribe", KAFKA_TOPIC) \
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
        .option("url", DB_URL) \
        .option("dbtable", TABLE_RAW_DATA) \
        .option("user", DB_USER) \
        .option("password", DB_PASSWORD) \
        .option("driver", DB_DRIVER) \
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
    # Scrive in staging
    batch_df.write \
        .format("jdbc") \
        .option("url", DB_URL) \
        .option("dbtable", TABLE_AGG_STAGING) \
        .option("user", DB_USER) \
        .option("password", DB_PASSWORD) \
        .option("driver", DB_DRIVER) \
        .mode("append") \
        .save()

    # Chiama stored procedure
    import pymysql
    conn = pymysql.connect(
        host="mysql",
        user=DB_USER,
        password=DB_PASSWORD,
        database="fireGuard360_db"
    )
    with conn.cursor() as cursor:
        cursor.execute("CALL upsert_sensor_analysis();")
    conn.commit()
    conn.close()

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
        .option("url", DB_URL) \
        .option("dbtable", TABLE_RISK_HISTORY) \
        .option("user", DB_USER) \
        .option("password", DB_PASSWORD) \
        .option("driver", DB_DRIVER) \
        .mode("append") \
        .save()

df_alerts.writeStream \
    .foreachBatch(write_alerts_to_mysql) \
    .outputMode("append") \
    .option("checkpointLocation", "/tmp/checkpoints/alerts") \
    .start()


# Avvia tutti i flussi
spark.streams.awaitAnyTermination()
