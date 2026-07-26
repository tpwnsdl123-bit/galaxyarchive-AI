import logging
import os
import threading

import torch
from huggingface_hub import snapshot_download
from sentence_transformers import SentenceTransformer

from config import ROOT_MODEL_DIR

model_loaded_event = threading.Event()

_model = None
MODEL_NAME = os.getenv(
    "EMBEDDING_MODEL_NAME",
    "Qwen/Qwen3-Embedding-0.6B",
)
MODEL_DIR_NAME = os.getenv(
    "EMBEDDING_MODEL_DIR_NAME",
    MODEL_NAME.replace("/", "__"),
)
MODEL_DIR = os.path.join(ROOT_MODEL_DIR, MODEL_DIR_NAME)


class EmbeddingModel:
    def __init__(self, model: SentenceTransformer):
        self._model = model

    def encode(
        self,
        texts: list[str],
        return_dense: bool = True,
        return_sparse: bool = False,
    ):
        dense_vecs = self._model.encode(
            texts,
            normalize_embeddings=True,
            convert_to_numpy=True,
        )

        if return_dense and not return_sparse:
            return {"dense_vecs": dense_vecs}

        return {"dense_vecs": dense_vecs}


def is_model_valid(path):
    return (
        os.path.exists(os.path.join(path, "config.json"))
        and os.path.exists(os.path.join(path, "modules.json"))
    )


def load_model():
    global _model
    if _model is not None:
        return _model

    if not is_model_valid(MODEL_DIR):
        logging.info("모델 다운로드 시작: %s -> %s", MODEL_NAME, MODEL_DIR)
        snapshot_download(repo_id=MODEL_NAME, local_dir=MODEL_DIR)
    else:
        logging.info("캐시된 모델 사용: %s", MODEL_DIR)

    try:
        device = "cuda" if torch.cuda.is_available() else "cpu"
        model = SentenceTransformer(
            MODEL_DIR,
            device=device,
            trust_remote_code=True,
            model_kwargs={
                "torch_dtype": torch.float16 if device == "cuda" else torch.float32,
            },
        )
        _model = EmbeddingModel(model)
        logging.info("임베딩 모델 로드 완료: %s", MODEL_NAME)

        model_loaded_event.set()

    except Exception:
        logging.critical("임베딩 모델 로드 실패: %s", MODEL_NAME, exc_info=True)
        raise

    return _model


def getModel():
    return load_model()
