from kiwipiepy import Kiwi
from FlagEmbedding import BGEM3FlagModel
import numpy as np

import logging
model = BGEM3FlagModel(
    model_name_or_path="./models/bge-m3",
    use_fp16=True
)

kiwi = Kiwi()
ALLOWED_TAGS = {"NNG","NNP","SL"}

def extract_keywords_rank(text:str, text_embedding:list[float],cnt:int=5):
    nouns = _extract_nouns(text)

    key_words = list(set(nouns))

    text_embedding = np.squeeze(text_embedding)
    keyword_embeddings = model.encode(key_words, return_dense=True)['dense_vecs']
    dot_products = np.dot(keyword_embeddings, text_embedding)

    # 분모: 각 벡터의 L2 노름(크기) 계산
    text_norm = np.linalg.norm(text_embedding)
    keyword_norms = np.linalg.norm(keyword_embeddings, axis=1)

    # 코사인 유사도 공식: (A · B) / (||A|| * ||B||)
    # 분모가 0이 되어 나누기 에러가 나는 것을 방지하기 위해 미세한 값(1e-8) 더하기
    scores = dot_products / (keyword_norms * text_norm + 1e-8)

    keyword_score_pairs = list(zip(key_words, scores))

    ranked_keywords = sorted(
        keyword_score_pairs,
        key=lambda x: x[1],
        reverse=True
    )[:cnt]

    keyword_score_pairs = [
        {
            "keyword": keyword,
            "score": float(score)
        }
        for keyword, score in ranked_keywords
    ]
    return keyword_score_pairs


def _extract_nouns(raw_text:str)->list[str]:
    tokens = kiwi.tokenize(raw_text)

    candidates = [
        token.form
        for token in tokens
        if token.tag in ALLOWED_TAGS
    ]

    return candidates