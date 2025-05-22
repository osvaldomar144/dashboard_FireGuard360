#!/bin/bash
echo "Attesa Kafka..."
sleep 10  # aspetta 10 secondi
kafka-topics.sh --create --topic sensordata --bootstrap-server kafka:9092 --partitions 1 --replication-factor 1 --if-not-exists