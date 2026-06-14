import threading

from confluent_kafka import Consumer, KafkaError
import json

from app.settings import (
    KAFKA_BOOTSTRAP_SERVERS,
    KAFKA_GROUP_ID
)

class KafkaConsumerManager:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if getattr(self, "_initialized", False):
            return

        self._initialized = True
        self._consumer_thread = None
        self._running = False
        self._handlers = {}

    def start(self, topics: list[str]):
        if self._running:
            print("[Kafka] already running")
            return

        self._running = True

        self._consumer_thread = threading.Thread(
            target=self._run_loop,
            args=(topics,),
            daemon=True
        )

        self._consumer_thread.start()

    def stop(self):
        self._running = False

    def _run_loop(self, topics: list[str]):
        
        consumer = Consumer({
            "bootstrap.servers": KAFKA_BOOTSTRAP_SERVERS,
            "group.id": KAFKA_GROUP_ID,
            "auto.offset.reset": "earliest"
        })

        consumer.subscribe(topics)

        try:
            while self._running:

                msg = consumer.poll(0.1)

                if msg is None:
                    continue
                
                error = msg.error()

                if error and error.code() == KafkaError._PARTITION_EOF:
                    continue
                else:
                    print(msg.error())

                topic = msg.topic()
                
                event = msg.value()
                if event is not None:
                    payload = event.decode("utf-8")
                    try:
                        payload = json.loads(payload)
                    except json.JSONDecodeError:
                        print(f"[Kafka] Invalid JSON in topic {topic}: {payload}")
                if topic is not None:
                    self._dispatch(topic, payload)    

        except Exception as e:
            print(f"[Kafka] {e}")

        finally:
            consumer.close()



    def register_handler(self, topic: str, handler):
        self._handlers[topic] = handler


    def _dispatch(self, topic: str, event: str):
        handler = self._handlers.get(topic)

        if handler:
            try:
                handler(event)
            except Exception as e:
                print(f"[Kafka] Handler error for topic {topic}: {e}")
        else:
            print(f"[Kafka] No handler registered for topic: {topic}")

kafka_consumer_manager = KafkaConsumerManager()