from pyspark.sql import SparkSession
from pyspark.sql.functions import from_json, col, window, avg, to_timestamp, lit, when, max as max_
from pyspark.sql.types import StructType, StringType, FloatType, TimestampType, IntegerType
from dotenv import load_dotenv
import os

load_dotenv(dotenv_path="CONFIG_FIREGUARD360.env")

# variabili configurazione per DB
DB_URL = os.getenv("DB_URL")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_DRIVER = os.getenv("DB_DRIVER")
TABLE_AGG_STAGING = os.getenv("TABLE_AGG_STAGING")
TABLE_RISK_STAGING = os.getenv("TABLE_RISK_STAGING")
TABLE_RISK_HISTORY = os.getenv("TABLE_RISK_HISTORY")
TABLE_RAW_STAGING = os.getenv("TABLE_RAW_STAGING")
WINDOW_DURATION = os.getenv("AGG_WINDOW_DURATION", "5 minutes")

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
    .add("timestamp", TimestampType()) \
    .add("danger_value", IntegerType())

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

# ========== 1. Aggregazioni per ora ========== #
df_agg = df_parsed \
    .withWatermark("timestamp", "2 minutes") \
    .groupBy(
        window(col("timestamp"), WINDOW_DURATION),
        col("sensor_id")
    ).agg(
        avg("temperature").alias("avg_temperature"),
        avg("humidity").alias("avg_humidity"),
        avg("gas").alias("avg_gas"),
        max_("temperature").alias("max_temperature"),
        max_("gas").alias("max_gas")
    ).select(
        col("sensor_id"),
        col("window.start").alias("window_start"),
        col("window.end").alias("window_end"),
        "avg_temperature", "avg_humidity", "avg_gas",
        "max_temperature", "max_gas"
    )

def write_agg_to_mysql(batch_df, batch_id):
    batch_df.write \
        .format("jdbc") \
        .option("url", DB_URL) \
        .option("dbtable", TABLE_AGG_STAGING) \
        .option("user", DB_USER) \
        .option("password", DB_PASSWORD) \
        .option("driver", DB_DRIVER) \
        .mode("append") \
        .save()

    import pymysql
    conn = pymysql.connect(
        host="mysql",
        user=DB_USER,
        password=DB_PASSWORD,
        database="fireGuard360_db"
    )
    with conn.cursor() as cursor:
        cursor.execute("CALL upsert_stats();")
    conn.commit()
    conn.close()

df_agg.writeStream \
    .foreachBatch(write_agg_to_mysql) \
    .outputMode("update") \
    .option("checkpointLocation", "/tmp/checkpoints/agg") \
    .start()


# ========== 2. Calcolo indice di rischio ========== #

df_risk = df_agg.withColumn("risk_score",
    (col("avg_temperature") * 0.4 + col("avg_gas") * 0.3 - col("avg_humidity") * 0.3)
).withColumn("risk_level", 
    when(col("risk_score") > 80, "critical")
    .when(col("risk_score") > 60, "high")
    .when(col("risk_score") > 40, "moderate")
    .otherwise("low")
).select(
    col("sensor_id"),
    col("risk_score"),
    col("risk_level"),
    col("window_end").alias("calculated_at")
)

def write_risk_to_mysql(batch_df, batch_id):
    batch_df.write \
        .format("jdbc") \
        .option("url", DB_URL) \
        .option("dbtable", TABLE_RISK_STAGING) \
        .option("user", DB_USER) \
        .option("password", DB_PASSWORD) \
        .option("driver", DB_DRIVER) \
        .mode("append") \
        .save()

    import pymysql
    conn = pymysql.connect(
        host="mysql",
        user=DB_USER,
        password=DB_PASSWORD,
        database="fireGuard360_db"
    )
    with conn.cursor() as cursor:
        cursor.execute("CALL upsert_risk_index();")
    conn.commit()
    conn.close()

df_risk.writeStream \
    .foreachBatch(write_risk_to_mysql) \
    .outputMode("update") \
    .option("checkpointLocation", "/tmp/checkpoints/risk") \
    .start()

# ========== 3. Alert rischio elevato (multi-condizioni) ========== #

df_alerts = df_parsed \
    .withColumn("alert_type",
        when((col("temperature") > 55), "Extreme Heat")
        .when((col("temperature") > 45) & (col("humidity") < 20), "High Fire Risk")
        .when(col("gas") > 900, "Gas Concentration Alert")
        .when(col("humidity") < 10, "Dry Environment")
        .otherwise(None)
    ) \
    .withColumn("description",
        when((col("temperature") > 55), "Temperature > 55°C")
        .when((col("temperature") > 45) & (col("humidity") < 20), "Temperature > 45°C and Humidity < 20%")
        .when(col("gas") > 900, "Gas levels exceed 900 PPM")
        .when(col("humidity") < 10, "Humidity < 10%")
        .otherwise(None)
    ) \
    .withColumn("severity",
        when((col("temperature") > 55), "critical")
        .when((col("temperature") > 45) & (col("humidity") < 20), "high")
        .when(col("gas") > 900, "moderate")
        .when(col("humidity") < 10, "low")
        .otherwise(None)
    ) \
    .filter(col("alert_type").isNotNull()) \
    .select(
        col("sensor_id"),
        col("alert_type"),
        col("description"),
        col("severity"),
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

# ========== 4. Scrittura dati grezzi su raw_sensor_data ========== #

def write_raw_to_mysql(batch_df, batch_id):
    batch_df.select(
        "sensor_id", "temperature", "humidity", "gas", "danger_value", "timestamp"
    ).withColumnRenamed("timestamp", "detected_at") \
     .write \
     .format("jdbc") \
     .option("url", DB_URL) \
     .option("dbtable", TABLE_RAW_STAGING) \
     .option("user", DB_USER) \
     .option("password", DB_PASSWORD) \
     .option("driver", DB_DRIVER) \
     .mode("append") \
     .save()

    import pymysql
    conn = pymysql.connect(
        host="mysql",
        user=DB_USER,
        password=DB_PASSWORD,
        database="fireGuard360_db"
    )
    with conn.cursor() as cursor:
        cursor.execute("CALL insert_raw_sensor_data();")
    conn.commit()
    conn.close()

df_parsed \
    .filter(col("danger_value").isNotNull()) \
    .writeStream \
    .foreachBatch(write_raw_to_mysql) \
    .outputMode("append") \
    .option("checkpointLocation", "/tmp/checkpoints/raw") \
    .start()

# Avvia tutti i flussi
spark.streams.awaitAnyTermination()
