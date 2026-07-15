from kiwipiepy import Kiwi
from model_configuration import getModel
import numpy as np

import logging
model = getModel()

kiwi = Kiwi()
ALLOWED_TAGS = {"NNG","NNP","SL"}

def extract_keywords_rank(title:str, text:str, text_embedding:list[float],cnt:int=5):
    nouns = _extract_nouns(title+text)

    keyword_map = {}

    #대소문자 중복 제거
    for noun in nouns:
        normalized_noun = noun.strip().lower()
        if not normalized_noun:
            continue
        if normalized_noun not in keyword_map:
            keyword_map[normalized_noun] = noun.strip()



    key_words = list(keyword_map.values())

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
        key=lambda x: (x[1], len(x[0])),
        reverse=True
    )

    # 포함관계 단어 제거
    selected_keywords = []
    for keyword, score in ranked_keywords:
        normalized_keyword = keyword.strip().lower()

        is_longer_duplicate = any(
            normalized_keyword != selected_keyword.strip().lower()
            and selected_keyword.strip().lower() in normalized_keyword
            for selected_keyword, _ in selected_keywords
        )

        if is_longer_duplicate:
            continue

        selected_keywords = [
            (selected_keyword, selected_score)
            for selected_keyword, selected_score in selected_keywords
            if not (
                    normalized_keyword != selected_keyword.strip().lower()
                    and normalized_keyword in selected_keyword.strip().lower()
            )
        ]

        selected_keywords.append((keyword, score))

        if len(selected_keywords) >= cnt:
            break

    keyword_score_pairs = [
        {
            "keyword": keyword,
            "score": float(score)
        }
        for keyword, score in selected_keywords
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
