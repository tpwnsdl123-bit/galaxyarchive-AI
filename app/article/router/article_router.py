from fastapi import APIRouter
    
# 컨트롤러 역할을 할 라우터 객체 생성 (prefix로 공통 엔드포인트 지정 가능)
router = APIRouter(prefix="/api/v1/articles", tags=["articles"])

@router.get("")
def get_articles():
    return { "message" : "list article test" }