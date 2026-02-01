import re
import pandas as pd
from review_analysis.preprocessing.base_processor import BaseDataProcessor

class ExampleProcessor(BaseDataProcessor):
    def __init__(self, input_path: str = None, output_dir: str = None):
        # 명세에 따라 초기화 인자는 유지하되, MongoDB 데이터를 직접 다룰 수 있게 합니다.
        super().__init__(input_path, output_dir)
        self.df = None

    def load_mongo_data(self, data: list):
        """MongoDB에서 가져온 딕셔너리 리스트를 DataFrame으로 변환"""
        self.df = pd.DataFrame(data)
        if "_id" in self.df.columns:
            self.df = self.df.drop(columns=["_id"])  # MongoDB 고유 ID 제거

    def preprocess(self):
        """데이터 전처리 수행 (예: 결측치 제거, 텍스트 정제)"""
        if self.df is None:
            return

        print("Preprocessing data...")
        # 1. 'text' 컬럼 전처리
        self.df['text'] = self.df['text'].str.strip()

        # 2. 결측치 처리
        self.df = self.df.dropna(subset=['text'])
        return self.df

    def feature_engineering(self):
        """
        피처 엔지니어링 수행
        - 파생변수 생성 및 텍스트 특성 추출
        """
        if self.df is None or self.df.empty:
            return

        print("Starting feature engineering...")

        # 1. 파생 변수 생성 (길이, 단어 수, 별점 그룹 등)
        self._create_derived_features()

        # 2. 텍스트 특성 추출 (이모지, URL 포함 여부)
        self._extract_content_flags()

        return self.df

    def _create_derived_features(self):
        """텍스트 및 날짜 관련 파생변수 생성"""
        # 텍스트 길이 및 단어 수
        self.df['text_len'] = self.df['text'].str.len()
        self.df['word_count'] = self.df['text'].str.split().str.len()

        # 별점 기반 긍정(1)/부정(0) 분류 (4점 이상을 긍정으로 간주)
        if 'rating' in self.df.columns:
            self.df['is_positive'] = (self.df['rating'] >= 4).astype(int)
            self.df['rating_group'] = pd.cut(
                self.df['rating'],
                bins=[0, 2, 3, 5],
                labels=['Low', 'Medium', 'High']
            )

        # 날짜 정보 분해 (date 컬럼이 있을 경우)
        if 'date' in self.df.columns:
            self.df['date'] = pd.to_datetime(self.df['date'], errors='coerce')
            self.df['year'] = self.df['date'].dt.year
            self.df['month'] = self.df['date'].dt.month
            self.df['weekday'] = self.df['date'].dt.day_name()

    def _extract_content_flags(self):
        """특수 콘텐츠 포함 여부 확인"""
        # 이모지 패턴 (간이 버전)
        emoji_pattern = re.compile(r'[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF]')
        # URL 패턴
        url_pattern = re.compile(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+')

        self.df['has_emoji'] = self.df['text'].apply(
            lambda x: 1 if emoji_pattern.search(str(x)) else 0
        )
        self.df['has_url'] = self.df['text'].apply(
            lambda x: 1 if url_pattern.search(str(x)) else 0
        )

    def get_processed_data(self) -> list:
        """전처리가 완료된 데이터를 다시 MongoDB에 넣기 위해 딕셔너리 리스트로 변환"""
        if self.df is not None:
            return self.df.to_dict('records')
        return []