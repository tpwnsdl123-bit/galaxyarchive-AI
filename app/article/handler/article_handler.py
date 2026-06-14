from app.messaging.KafakaConsumerManager import KafkaConsumerManager


kafka_consumer_manager = KafkaConsumerManager()

kafka_consumer_manager.register_handler("article-events", lambda event: print(f"[ARTICLE-EVENTS] {event}"))