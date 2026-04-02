from pyspark.sql import SparkSession
from pyspark.sql.functions import from_json, col, avg, max as spark_max
from pyspark.sql.types import StructType, StringType, DoubleType

# --- Schema ---
schema = StructType() \
    .add("symbol", StringType()) \
    .add("price", DoubleType()) \
    .add("timestamp", StringType())

#PostgreSQL config 
PG_URL = "jdbc:postgresql://postgres:5432/stockdb"
PG_PROPERTIES = {
    "user": "stockuser",
    "password": "stockpass",
    "driver": "org.postgresql.Driver"
}

def create_spark_session():
    return SparkSession.builder \
        .appName("StockMarketProcessor") \
        .config("spark.jars.packages",
                "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0") \
        .config("spark.jars", "/opt/spark-apps/postgresql-42.6.0.jar") \
        .getOrCreate()

def write_to_postgres(batch_df, batch_id):
    """This function is called once per micro-batch."""
    if batch_df.count() == 0:
        return

    print(f"Writing batch {batch_id} to PostgreSQL...")
    batch_df.write \
        .jdbc(url=PG_URL,
              table="stock_prices",
              mode="append",
              properties=PG_PROPERTIES)
    print(f"Batch {batch_id} written successfully.")

def run():
    spark = create_spark_session()
    spark.sparkContext.setLogLevel("WARN")

    #Read from Kafka  
    raw_stream = spark.readStream \
        .format("kafka") \
        .option("kafka.bootstrap.servers", "kafka:9092") \
        .option("subscribe", "stock-prices") \
        .option("startingOffsets", "latest") \
        .load()

    #Parse JSON messages 
    parsed = raw_stream \
        .selectExpr("CAST(value AS STRING) as json_str") \
        .select(from_json(col("json_str"), schema).alias("data")) \
        .select("data.*")

    #Aggregate 
    aggregated = parsed \
        .groupBy("symbol") \
        .agg(
            avg("price").alias("avg_price"),
            spark_max("price").alias("latest_price")
        )

    #Write to PostgreSQL using foreachBatch
    query = aggregated.writeStream \
        .outputMode("complete") \
        .foreachBatch(write_to_postgres) \
        .trigger(processingTime="10 seconds") \
        .start()

    query.awaitTermination()

if __name__ == "__main__":
    run()