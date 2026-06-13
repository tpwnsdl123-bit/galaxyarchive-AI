
import threading
from confluent_kafka import Consumer, KafkaError

class KafkaConsumerManager:
    def __init__(self, consumer):
        self.consumer = consumer
    
    def _run_loop(self, topic):
        config = {
            'bootstrap.servers': KAFKA_BOOTSTRAP_SERVERS,
            'group.id': 'galaxy-archive-ai-group',
            'auto.offset.reset': 'earliest'
        }
        self.consumer = Consumer(config)
        self.consumer.subscribe([topic])


        try:
            while True:
                msg = self.consumer.poll(1.0)

                if msg is None:
                    continue
                if msg.error():
                    if msg.error().code() == KafkaError._PARTITION_EOF:
                        continue
                    else:
                        print(f"Kafka error: {msg.error()}")
                        break
                
                event = msg.value().decode('utf-8')
                print(f"Received event: {event}")
        
        except Exception as e:
            print(f"Error in Kafka consumer loop: {e}")
        finally:
            self.consumer.close()
    
    def listen_event(self, topic):
        thread = threading.Thread(target=self._run_loop, args=(topic,), daemon=True)
        thread.start()
        print(f"🚀 [Kafka Consumer] Thread for topic '{topic}' successfully detached.")

#외부 import instance
kafka_shared_consumer = KafkaConsumerManager()