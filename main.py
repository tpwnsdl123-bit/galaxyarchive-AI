import logging
import article_created.handler.article_created_handler
LOG_FORMAT = "[%(asctime)s] %(levelname)s in %(module)s: %(message)s"

logging.basicConfig(
    level=logging.DEBUG,
    format=LOG_FORMAT,
    force=True
)

from consumer.worker import run_consumer





if __name__ == '__main__':

    logging.info("Starting Kafka Consumer")
    run_consumer()