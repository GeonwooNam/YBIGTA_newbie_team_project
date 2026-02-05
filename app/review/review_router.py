from fastapi import APIRouter, HTTPException
from database.mongodb_connection import mongo_db
from review_analysis.preprocessing.example_processor import ExampleProcessor

router = APIRouter(prefix="/review", tags=["Review"])


@router.post("/preprocess/{site_name}")
async def preprocess_reviews(site_name: str):
    """
    MongoDB에서 크롤링 데이터를 조회하여 전처리 및 피처 엔지니어링을 수행한 뒤 저장하는 API
    """
    try:
        # 1. MongoDB에서 해당 사이트의 원본 크롤링 데이터 조회
        collection = mongo_db[site_name]
        raw_reviews = list(collection.find())

        if not raw_reviews:
            return {"status": "error", "message": f"No data found for collection: {site_name}"}

        # 2. 전처리 클래스(ExampleProcessor) 객체 생성 및 로직 실행
        # input_path와 output_dir은 파일 기반 작업이 아니므로 None으로 설정 가능합니다.
        processor = ExampleProcessor()

        # 데이터 로드 (내부적으로 DataFrame 변환 및 _id 제거 수행)
        processor.load_mongo_data(raw_reviews)

        # 전처리 수행 (컬럼명 통일, 결측치 제거 등)
        processor.preprocess()

        # 피처 엔지니어링 수행 (긍정/부정 분류, 별점 그룹화, 텍스트 특성 추출 등)
        processor.feature_engineering()

        # 최종 결과물 리스트(dict 형태) 가져오기
        processed_data = processor.get_processed_data()

        # 3. 전처리된 데이터를 MongoDB에 저장 (컬렉션명: {site_name}_preprocessed)
        target_collection_name = f"{site_name}_preprocessed"
        target_collection = mongo_db[target_collection_name]

        if processed_data:
            # 기존에 전처리된 데이터가 있다면 삭제 후 새로 삽입 (중복 방지)
            target_collection.delete_many({})
            target_collection.insert_many(processed_data)

        return {
            "status": "success",
            "message": f"Successfully preprocessed {len(processed_data)} reviews for {site_name}",
            "target_collection": target_collection_name
        }

    except Exception as e:
        # 에러 발생 시 500 에러와 함께 메시지 반환
        raise HTTPException(status_code=500, detail=f"Preprocessing failed: {str(e)}")