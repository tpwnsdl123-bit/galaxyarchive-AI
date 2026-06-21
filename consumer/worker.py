import json
import logging
from typing import Dict, Callable

from consumer.kafka_consumer import KafkaConsumer
from confluent_kafka import Message, KafkaError

kafka_consumer = KafkaConsumer(bootstrap_servers='localhost:9092',group_id='embedding-worker')
kafka_consumer.subscribe(['article-created'])

handler_dispatcher:Dict[str, Callable] = {}

def run_consumer():
    try:
        while True:
            msg: Message|None = kafka_consumer.poll(1.0)

            if msg is None:
                continue

            if msg.error():
                if msg.error().code() == KafkaError._PARTITION_EOF:
                    continue

                logging.error("Kafka error topic=%s partition=%s error=%s", msg.topic(), msg.partition(), msg.error())
                continue

            _dispatch_msg(msg.topic(),_parse_msg(msg))

    except KeyboardInterrupt:
        kafka_consumer.close()
        logging.info("Kafka consumer stopped by keyboardInterrupt")
    except Exception as e:
        logging.exception(e)

    finally:
        logging.info("Kafka consumer stopped by keyboardInterrupt")

def _parse_msg(msg: Message)->dict | None:
    try:
        payload_str = msg.value().decode('utf-8')
        payload = json.loads(payload_str)
        return payload

    except UnicodeDecodeError as ue:
        logging.error("메시지 디코딩(utf-8) 실패: %s", ue)
        return None
    except json.JSONDecodeError as je:
        logging.error("JSON 파싱 에러 (올바른 JSON 형식이 아님): %s", je)
        return None
    except Exception as e:
        logging.error("메시지 파싱 중 예상치 못한 에러: %s", e, exc_info=True)
        return None

def handler(topic:str):
    def wrapper(func):
        handler_dispatcher[topic] = func
        return func
    return wrapper

def _dispatch_msg(topic,payload):
    if handler_dispatcher.get(topic) is None:
        logging.error("not registered topic handler %s", topic)
        return

    handler_dispatcher[topic](payload)