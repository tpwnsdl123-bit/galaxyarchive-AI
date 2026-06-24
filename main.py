import logging


LOG_FORMAT = "[%(asctime)s] %(levelname)s in %(module)s: %(message)s"

from config import(
    LOG_LEVEL
)

logging.basicConfig(
    level=LOG_LEVEL,
    format=LOG_FORMAT,
    force=True
)
import article_created.handler.article_created_handler
import model_configuration
from consumer.worker import run_consumer


if __name__ == '__main__':

    logging.info("Starting Kafka Consumer")
    run_consumer()
