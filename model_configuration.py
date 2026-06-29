import logging
import os
import threading

import torch
from FlagEmbedding import BGEM3FlagModel
from huggingface_hub import snapshot_download
from config import ROOT_MODEL_DIR

model_loaded_event = threading.Event()

# 전역 변수 초기화
_model = None
MODEL_DIR = os.path.join(ROOT_MODEL_DIR, "bge-m3")
MODEL_NAME = "BAAI/bge-m3"

def is_model_valid(path):
    return os.path.exists(os.path.join(path, "config.json"))

def load_model():
    global _model
    if _model is not None:
        return _model

    if not is_model_valid(MODEL_DIR):
        logging.info(f"모델 다운로드 시작: {MODEL_NAME}")
        snapshot_download(repo_id=MODEL_NAME, local_dir=MODEL_DIR)

    try:
        device = 'cuda' if torch.cuda.is_available() else 'cpu'
        _model = BGEM3FlagModel(
            model_name_or_path=MODEL_DIR,
            use_fp16=True,
            device=device  # 명시적 설정 권장
        )
        logging.info("BGE-M3 모델 로드 완료")

        #모델 로드후 thread blocking 해제 이벤트 발행
        model_loaded_event.set()

    except Exception:
        logging.critical("BGE-M3 모델 로드 실패", exc_info=True)
        raise
    
    return _model

def getModel():
    return load_model()
