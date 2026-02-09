"""FAISS 인덱스 빌드 스크립트 — 로컬에서 한 번 실행하여 인덱스 생성"""
import os
import pandas as pd
from langchain_community.vectorstores import FAISS
from langchain_upstage import UpstageEmbeddings
from langchain.schema import Document

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DB_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "db", "faiss_index")

CSV_FILES = [
    ("database/preprocessed_reviews_google.csv", "google"),
    ("database/preprocessed_reviews_kakao.csv", "kakao"),
    ("database/preprocessed_reviews_tripcom.csv", "tripcom"),
]


def build_index():
    api_key = os.getenv("UPSTAGE_API_KEY")
    if not api_key:
        raise ValueError("UPSTAGE_API_KEY 환경변수를 설정해주세요.")

    documents = []
    for csv_path, platform in CSV_FILES:
        full_path = os.path.join(BASE_DIR, csv_path)
        df = pd.read_csv(full_path, encoding="utf-8-sig")
        for _, row in df.iterrows():
            text = str(row.get("context_cleaned", "")).strip()
            if not text:
                continue
            metadata = {
                "platform": platform,
                "rating": str(row.get("rating", "")),
                "date": str(row.get("date", "")),
                "rating_group": str(row.get("rating_group", "")),
            }
            documents.append(Document(page_content=text, metadata=metadata))

    print(f"총 {len(documents)}개 문서 로드 완료. 임베딩 생성 중...")

    embeddings = UpstageEmbeddings(model="solar-embedding-1-large", api_key=api_key)
    vectorstore = FAISS.from_documents(documents, embeddings)

    os.makedirs(DB_DIR, exist_ok=True)
    vectorstore.save_local(DB_DIR)
    print(f"FAISS 인덱스 저장 완료: {DB_DIR}")


if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    build_index()
