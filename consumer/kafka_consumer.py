import logging
from confluent_kafka import Consumer,Message

from config import(
    KAFKA_BOOTSTRAP_SERVERS,
    KAFKA_GROUP_ID
)


class KafkaConsumer:
    def __init__(self, bootstrap_servers:str, group_id: str):
        try:
            self.consumer = Consumer({
                "bootstrap.servers": bootstrap_servers,
                "group.id": group_id,
                "auto.offset.reset": "earliest",
                "enable.auto.commit": "false",
            })

            logging.info("kafka connected successfully")

        except Exception as e:
            logging.error("kafka connect fail ",exc_info=True)
            raise e

    def subscribe(self, topics: list[str])->None:
        self.consumer.subscribe(topics)

    def poll(self, poll_interval: float)->Message | None:
        return self.consumer.poll(poll_interval)

    def close(self)->None:
        self.consumer.close()

    def commit(self):
        self.consumer.commit()

kafka_consumer = KafkaConsumer(bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,group_id=KAFKA_GROUP_ID)