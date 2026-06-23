import logging
import os.path
import torch
from FlagEmbedding import BGEM3FlagModel
from huggingface_hub import snapshot_download


from config import(
    ROOT_MODEL_DIR,
)



MODEL_DIR = ROOT_MODEL_DIR+"/bge-m3"
MODEL_NAME = "BAAI/bge-m3"


device = 'cuda' if torch.cuda.is_available() else 'cpu'


def is_model_valid(path):
    return os.path.exists(os.path.join(path, "config.json"))


if not is_model_valid(MODEL_DIR):
    snapshot_download(
        repo_id=MODEL_NAME,
        local_dir=MODEL_DIR,
    )
try:
    model = BGEM3FlagModel(
        model_name_or_path=MODEL_DIR,
        use_fp16=True
    )

    logging.info("BGE-M3 모델 로드 완료")

except Exception:
    logging.critical(
        "BGE-M3 모델 로드 실패",
        exc_info=True
    )
    raise

