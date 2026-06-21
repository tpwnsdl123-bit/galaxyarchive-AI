from FlagEmbedding import BGEM3FlagModel

import logging

model = BGEM3FlagModel(
    model_name_or_path="./models/bge-m3",
    use_fp16=True
)

def embedding(title:str,raw_text:str):
    text = f"{title}\n{raw_text}"
    vector = model.encode([text])
    logging.info("vector: {}".format(vector))
    return vector["dense_vecs"]