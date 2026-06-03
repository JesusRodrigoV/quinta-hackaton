import os

NEO4J_URI = os.getenv("NEO4J_URI", "bolt://neo4j:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")
KAFKA_BROKER = os.getenv("KAFKA_BROKER", "")
KAFKA_TOPIC_BUS_LOCATION_UPDATED = os.getenv("KAFKA_TOPIC_BUS_LOCATION_UPDATED", "bus-location-updated")
KAFKA_CONSUMER_GROUP_ID = os.getenv("KAFKA_CONSUMER_GROUP_ID", "routing-service-bus-tracker")
