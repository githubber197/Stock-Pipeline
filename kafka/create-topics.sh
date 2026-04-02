#!/bin/bash
echo "Waiting for Kafka to be ready..."
cub kafka-ready -b kafka:9092 1 30

echo "Creating topic..."
kafka-topics --create \
  --if-not-exists \
  --topic stock-prices \
  --bootstrap-server kafka:9092 \
  --partitions 1 \
  --replication-factor 1

echo "Topic created successfully."
kafka-topics --list --bootstrap-server kafka:9092