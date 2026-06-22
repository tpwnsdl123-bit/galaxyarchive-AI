from confluent_kafka import Producer
import json
import logging

from config import(
    KAFKA_BOOTSTRAP_SERVERS,
)


class KafkaPublisher:
    def __init__(self, bootstrap_servers):
        try:
            self.producer = Producer({"bootstrap.servers" : bootstrap_servers})

            logging.info("Kafka producer initialized")

        except Exception as e:
            logging.error("kafka producer initialization failed",exc_info=True)
            raise e

    def publish_message(self, topic:str, message):
        try:
            self.producer.produce(topic, value=json.dumps(message).encode("utf-8"))
            self.producer.poll(0)
        except Exception as e:
            logging.error("kafka producer initialization failed",exc_info=True)
            raise e

    def close(self):
        self.producer.flush()

kafka_publisher = KafkaPublisher(KAFKA_BOOTSTRAP_SERVERS)