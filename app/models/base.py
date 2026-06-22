from abc import ABC, abstractmethod
from typing import List

#기능별 함수 안내판
class BaseEmbeddingModel(ABC):

    @abstractmethod
    # todo
    def embed_text(self, text: str):
        """
        사용자가 쓴 개시글을 임베딩 값으로 바꿔주는 함수
        """
        pass