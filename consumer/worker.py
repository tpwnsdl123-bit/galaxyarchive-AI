import json
import logging
from typing import Dict, Callable

from consumer.kafka_consumer import kafka_consumer
from confluent_kafka import Message, KafkaError
from model_configuration import model_loaded_event

kafka_consumer.subscribe(topics=['article-created'])

handler_dispatcher:Dict[str, Callable] = {}

def run_consumer():
    try:
        #임베딩 모델 로드 완료 까지 blocking
        model_loaded_event.wait()

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
        raise ue
    except json.JSONDecodeError as je:
        logging.error("JSON 파싱 에러 (올바른 JSON 형식이 아님): %s", je)
        raise je
    except Exception as e:
        logging.error("메시지 파싱 중 예상치 못한 에러: %s", e, exc_info=True)
        raise e

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