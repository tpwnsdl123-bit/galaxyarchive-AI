from dotenv import load_dotenv
import os

load_dotenv()

KAFKA_BOOTSTRAP_SERVERS = os.getenv(
    "KAFKA_BOOTSTRAP_SERVERS",
    "localhost:9092"
)

KAFKA_GROUP_ID = os.getenv(
    "KAFKA_GROUP_ID",
    "embedding-worker"
)

ROOT_MODEL_DIR = os.getenv(
    "ROOT_MODEL_DIR",
    "./models"
)

LOG_LEVEL = os.getenv(
    "LOG_LEVEL",
    10
)