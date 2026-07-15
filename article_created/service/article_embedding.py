from FlagEmbedding import BGEM3FlagModel
from model_configuration import getModel
import logging

model = getModel()

def embedding(title:str,raw_text:str):
    text = f"{title}\n{raw_text}"
    vector = model.encode(
        [text],
        return_dense=True,
        return_sparse=False)
    return vector["dense_vecs"]
