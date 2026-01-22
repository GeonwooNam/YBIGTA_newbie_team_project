"""
Trip.com 리뷰 데이터 전처리 및 피처 엔지니어링 모듈
"""
import pandas as pd
import numpy as np
import re
from datetime import datetime
from typing import Optional
import os

from review_analysis.preprocessing.base_processor import BaseDataProcessor


class TripComProcessor(BaseDataProcessor):
    """
    Trip.com 리뷰 데이터를 전처리하고 피처 엔지니어링을 수행하는 클래스
    """
    
    def __init__(self, input_path: str, output_dir: str):
        super().__init__(input_path, output_dir)
        self.df: Optional[pd.DataFrame] = None
        self.processed_df: Optional[pd.DataFrame] = None
        
    def preprocess(self):
        """
        데이터 전처리 수행
        - 칼럼명 통일 (text -> context)
        - 날짜 데이터 형식 변환
        - 결측치 처리
        - 이상치 처리
        - 텍스트 전처리
        """
        print(f"Loading data from {self.input_path}...")
        self.df = pd.read_csv(self.input_path)
        print(f"Original data shape: {self.df.shape}")
        
        # 1. 칼럼명 통일 (text -> context)
        print("\n[1] 칼럼명 통일 중...")
        if 'text' in self.df.columns:
            self.df = self.df.rename(columns={'text': 'context'})
        elif 'content' in self.df.columns:
            self.df = self.df.rename(columns={'content': 'context'})
        print(f"  - 칼럼명 통일 완료: context")
        
        # 2. 날짜 데이터 형식 변환
        print("\n[2] 날짜 데이터 형식 변환 중...")
        self.df['date'] = pd.to_datetime(self.df['date'], errors='coerce', format='%b %d, %Y')
        print(f"  - 날짜 형식 변환 완료")
        
        # 3. 결측치 처리
        print("\n[3] 결측치 처리 중...")
        initial_count = len(self.df)
        
        # rating 결측치: 평균값으로 대체
        if self.df['rating'].isna().any():
            rating_mean = self.df['rating'].mean()
            self.df['rating'] = self.df['rating'].fillna(rating_mean)
            print(f"  - rating 결측치 평균값으로 대체: {self.df['rating'].isna().sum()}개")
        
        # context, date 결측치: 해당 행 삭제
        before_drop = len(self.df)
        self.df = self.df.dropna(subset=['context', 'date'])
        dropped = before_drop - len(self.df)
        if dropped > 0:
            print(f"  - context/date 결측치 제거: {dropped}개 행 삭제")
        
        print(f"  - 결측치 처리 완료: {initial_count} -> {len(self.df)} rows")
        
        # 4. 이상치 처리
        print("\n[4] 이상치 처리 중...")
        self._handle_outliers()
        
        # 5. 텍스트 전처리
        print("\n[5] 텍스트 전처리 중...")
        self._preprocess_text()
        
        print(f"\n전처리 완료. 최종 데이터 shape: {self.df.shape}")
        self.processed_df = self.df.copy()
    
    def _handle_outliers(self):
        """
        이상치 처리
        - 기간 이상치: 2019년 이전 데이터 제거
        - 텍스트 이상치: 3자 미만(2자 이하) 리뷰 제거
        """
        initial_count = len(self.df)
        
        # 기간 이상치: 2019년 이전 및 2026년 이후 제거
        self.df['year'] = self.df['date'].dt.year
        date_outliers = (self.df['year'] < 2019) | (self.df['year'] > 2026)
        self.df = self.df[~date_outliers]
        print(f"  - 기간 이상치 제거 (2019년 이전, 2026년 이후): {date_outliers.sum()}개")
        
        # 텍스트 이상치: 3자 미만(2자 이하) 리뷰 제거
        text_length = self.df['context'].str.len()
        text_outliers = text_length < 3
        self.df = self.df[~text_outliers]
        print(f"  - 텍스트 이상치 제거 (3자 미만): {text_outliers.sum()}개")
        
        print(f"  - 총 이상치 제거: {initial_count} -> {len(self.df)} rows")
    
    def _preprocess_text(self):
        """
        텍스트 전처리
        - 줄바꿈을 공백으로 변환
        - 연속된 공백을 하나로
        - 앞뒤 공백 제거
        """
        def clean_text(text: str) -> str:
            if pd.isna(text):
                return ""
            
            text = str(text)
            # 줄바꿈을 공백으로 변환
            text = text.replace('\n', ' ').replace('\r', ' ')
            # 연속된 공백을 하나로
            text = re.sub(r'\s+', ' ', text)
            # 앞뒤 공백 제거
            text = text.strip()
            return text
        
        self.df['context_cleaned'] = self.df['context'].apply(clean_text)
        # 빈 텍스트 제거
        self.df = self.df[self.df['context_cleaned'].str.len() > 0]
        print(f"  - 텍스트 전처리 완료: {len(self.df)} rows")
    
    def feature_engineering(self):
        """
        피처 엔지니어링 수행
        - 파생 변수 생성
        - 텍스트 벡터화
        """
        if self.processed_df is None:
            raise ValueError("전처리를 먼저 수행해주세요.")
        
        print("\n[6] 피처 엔지니어링 중...")
        self.df = self.processed_df.copy()
        
        # 파생 변수 생성
        self._create_derived_features()
        
        # 텍스트 벡터화
        self._vectorize_text()
        
        print(f"\n피처 엔지니어링 완료. 최종 데이터 shape: {self.df.shape}")
    
    def _create_derived_features(self):
        """
        파생 변수 생성
        - text_len: 텍스트 길이 (문자 수)
        - word_count: 단어 수
        - rating_group: 별점 그룹 (낮음/보통/높음)
        - year, month, day, weekday: 날짜 관련 변수
        - year_month: 연도-월
        - is_positive: 긍정 리뷰 여부 (별점 4 이상)
        - text_has_emoji: 이모지 포함 여부
        - text_has_url: URL 포함 여부
        """
        # 텍스트 길이 관련
        self.df['text_len'] = self.df['context_cleaned'].str.len()
        self.df['word_count'] = self.df['context_cleaned'].str.split().str.len()
        
        # 별점 관련
        self.df['rating_group'] = pd.cut(
            self.df['rating'],
            bins=[0, 2, 3, 5],
            labels=['낮음(1-2)', '보통(3)', '높음(4-5)']
        )
        self.df['is_positive'] = (self.df['rating'] >= 4).astype(int)
        
        # 날짜 관련
        self.df['year'] = self.df['date'].dt.year
        self.df['month'] = self.df['date'].dt.month
        self.df['day'] = self.df['date'].dt.day
        self.df['weekday'] = self.df['date'].dt.day_name()
        self.df['weekday_num'] = self.df['date'].dt.dayofweek  # 0=월요일, 6=일요일
        self.df['year_month'] = self.df['date'].dt.to_period('M').astype(str)
        
        # 텍스트 특성
        # 이모지 포함 여부 (간단한 체크)
        emoji_pattern = re.compile(
            "["
            "\U0001F600-\U0001F64F"  # emoticons
            "\U0001F300-\U0001F5FF"  # symbols & pictographs
            "\U0001F680-\U0001F6FF"  # transport & map symbols
            "\U0001F1E0-\U0001F1FF"  # flags
            "\U00002702-\U000027B0"
            "\U000024C2-\U0001F251"
            "]+", flags=re.UNICODE
        )
        self.df['text_has_emoji'] = self.df['context_cleaned'].apply(
            lambda x: 1 if emoji_pattern.search(str(x)) else 0
        )
        
        # URL 포함 여부
        url_pattern = re.compile(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+')
        self.df['text_has_url'] = self.df['context_cleaned'].apply(
            lambda x: 1 if url_pattern.search(str(x)) else 0
        )
        
        print("  - 파생 변수 생성 완료:")
        print(f"    * 텍스트: text_len, word_count")
        print(f"    * 별점: rating_group, is_positive")
        print(f"    * 날짜: year, month, day, weekday, year_month")
        print(f"    * 텍스트 특성: text_has_emoji, text_has_url")
    
    def _vectorize_text(self):
        """
        텍스트 벡터화
        - TF-IDF 벡터화 수행 (추천 방법)
        """
        try:
            from sklearn.feature_extraction.text import TfidfVectorizer
            from sklearn.decomposition import TruncatedSVD
            
            # TF-IDF 벡터화
            print("  - TF-IDF 벡터화 수행 중...")
            tfidf = TfidfVectorizer(
                max_features=100,  # 상위 100개 단어만 사용
                stop_words='english',  # 영어 불용어 제거
                ngram_range=(1, 2),  # 1-gram과 2-gram 사용
                min_df=2,  # 최소 2개 문서에 등장해야 함
                max_df=0.95  # 95% 이상 문서에 등장하면 제외
            )
            
            tfidf_matrix = tfidf.fit_transform(self.df['context_cleaned'])
            
            # 차원 축소 (20차원으로 축소)
            print("  - 차원 축소 수행 중...")
            svd = TruncatedSVD(n_components=20, random_state=42)
            text_vectors = svd.fit_transform(tfidf_matrix)
            
            # 벡터를 데이터프레임에 추가
            for i in range(text_vectors.shape[1]):
                self.df[f'tfidf_vector_{i+1}'] = text_vectors[:, i]
            
            # 주요 키워드 저장 (각 리뷰별 상위 5개 키워드)
            feature_names = tfidf.get_feature_names_out()
            self.df['top_keywords'] = self.df['context_cleaned'].apply(
                lambda x: self._extract_top_keywords(x, tfidf, feature_names)
            )
            
            print(f"  - TF-IDF 벡터화 완료: {text_vectors.shape[1]}차원 벡터 생성")
            print(f"  - 주요 키워드 추출 완료")
            
        except ImportError:
            print("  - 경고: sklearn이 설치되지 않아 텍스트 벡터화를 건너뜁니다.")
            print("    pip install scikit-learn으로 설치해주세요.")
    
    def _extract_top_keywords(self, text: str, vectorizer, feature_names, top_n: int = 5) -> str:
        """
        텍스트에서 상위 키워드 추출
        """
        try:
            tfidf_scores = vectorizer.transform([text])
            feature_index = tfidf_scores[0, :].nonzero()[1]
            tfidf_scores = zip(feature_index, [tfidf_scores[0, x] for x in feature_index])
            sorted_scores = sorted(tfidf_scores, key=lambda x: x[1], reverse=True)
            top_keywords = [feature_names[i] for i, _ in sorted_scores[:top_n]]
            return ', '.join(top_keywords)
        except:
            return ""
    
    def save_to_database(self):
        """
        전처리된 데이터를 CSV 파일로 저장
        파일명: preprocessed_reviews_tripcom.csv
        """
        if self.df is None:
            raise ValueError("전처리 및 피처 엔지니어링을 먼저 수행해주세요.")
        
        # 저장할 컬럼 선택 (원본 데이터 + 파생 변수)
        columns_to_save = [
            'rating', 'date', 'context', 'context_cleaned',
            'text_len', 'word_count',
            'rating_group', 'is_positive',
            'year', 'month', 'day', 'weekday', 'weekday_num', 'year_month',
            'text_has_emoji', 'text_has_url',
            'top_keywords'
        ]
        
        # TF-IDF 벡터 컬럼 추가
        tfidf_columns = [col for col in self.df.columns if col.startswith('tfidf_vector_')]
        columns_to_save.extend(tfidf_columns)
        
        # 존재하는 컬럼만 선택
        available_columns = [col for col in columns_to_save if col in self.df.columns]
        output_df = self.df[available_columns].copy()
        
        # 출력 파일 경로
        output_path = os.path.join(self.output_dir, 'preprocessed_reviews_tripcom.csv')
        
        # 디렉토리 생성
        os.makedirs(self.output_dir, exist_ok=True)
        
        # CSV 저장
        output_df.to_csv(output_path, index=False, encoding='utf-8-sig')
        print(f"\n[7] 결과 저장 완료: {output_path}")
        print(f"  - 저장된 행 수: {len(output_df)}")
        print(f"  - 저장된 컬럼 수: {len(output_df.columns)}")
