"""
Google Maps 리뷰 데이터 전처리 및 피처 엔지니어링 모듈
한글 형태소 분석 지원
"""
import pandas as pd
import numpy as np
import re
from datetime import datetime
from typing import Optional
import os

from review_analysis.preprocessing.base_processor import BaseDataProcessor
from review_analysis.preprocessing.korean_tokenizer import (
    preprocess_korean_text,
    detect_language,
    get_korean_stopwords
)


class GoogleProcessor(BaseDataProcessor):
    """
    Google Maps 리뷰 데이터를 전처리하고 피처 엔지니어링을 수행하는 클래스
    """
    
    def __init__(self, input_path: str, output_dir: str):
        super().__init__(input_path, output_dir)
        self.df: Optional[pd.DataFrame] = None
        self.processed_df: Optional[pd.DataFrame] = None
        
    def preprocess(self):
        """
        데이터 전처리 수행
        - 칼럼명 통일 (content -> context)
        - 날짜 데이터 형식 변환
        - 결측치 처리
        - 이상치 처리
        - 텍스트 전처리 (한글 형태소 분석 포함)
        """
        print(f"Loading data from {self.input_path}...")
        self.df = pd.read_csv(self.input_path)
        print(f"Original data shape: {self.df.shape}")
        
        # 1. 칼럼명 통일 (content -> context)
        print("\n[1] 칼럼명 통일 중...")
        if 'content' in self.df.columns:
            self.df = self.df.rename(columns={'content': 'context'})
        elif 'text' in self.df.columns:
            self.df = self.df.rename(columns={'text': 'context'})
        print(f"  - 칼럼명 통일 완료: context")
        
        # 2. 날짜 데이터 형식 변환
        print("\n[2] 날짜 데이터 형식 변환 중...")
        # Google Maps 날짜 형식: 2026.1.10. 또는 2026.01.10.
        self.df['date'] = pd.to_datetime(
            self.df['date'].str.replace('.', '-', regex=False).str.rstrip('-'),
            errors='coerce',
            format='%Y-%m-%d'
        )
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
        
        # 5. 텍스트 전처리 (한글 형태소 분석 포함)
        print("\n[5] 텍스트 전처리 및 형태소 분석 중...")
        self._preprocess_text()
        
        print(f"\n전처리 완료. 최종 데이터 shape: {self.df.shape}")
        self.processed_df = self.df.copy()
    
    def _handle_outliers(self):
        """
        이상치 처리
        - 기간 이상치: 2019년 이전 및 2026년 이후 데이터 제거
        - 별점 이상치: 1.0~5.0 범위 벗어난 값 제거
        - 텍스트 이상치: 3자 미만(2자 이하) 리뷰 제거
        """
        initial_count = len(self.df)
        
        # 별점 이상치: 1.0~5.0 범위 벗어난 값 제거
        rating_outliers = (self.df['rating'] < 1.0) | (self.df['rating'] > 5.0)
        self.df = self.df[~rating_outliers]
        print(f"  - 별점 이상치 제거: {rating_outliers.sum()}개")
        
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
        텍스트 전처리 및 한글 형태소 분석
        - 줄바꿈을 공백으로 변환
        - 연속된 공백을 하나로
        - 앞뒤 공백 제거
        - 한글 형태소 분석 적용
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
        
        # 기본 텍스트 정제
        self.df['context_cleaned'] = self.df['context'].apply(clean_text)
        
        # 한글 형태소 분석 적용
        print("  - 한글 형태소 분석 수행 중...")
        self.df['context_tokenized'] = self.df['context_cleaned'].apply(
            lambda x: preprocess_korean_text(x, use_morphology=True)
        )
        
        # 빈 텍스트 제거
        empty_text = self.df['context_tokenized'].str.len() == 0
        if empty_text.any():
            self.df = self.df[~empty_text]
            print(f"  - 빈 텍스트 제거: {empty_text.sum()}개")
        
        print(f"  - 텍스트 전처리 완료")
    
    def feature_engineering(self):
        """
        피처 엔지니어링 수행
        - 파생 변수 생성
        - 텍스트 벡터화 (한글 지원)
        """
        print("\n[피처 엔지니어링 시작]")
        
        # 파생 변수 생성
        self._create_derived_features()
        
        # 텍스트 벡터화
        self._vectorize_text()
        
        # processed_df 업데이트
        self.processed_df = self.df.copy()
        
        print("\n피처 엔지니어링 완료.")
    
    def _create_derived_features(self):
        """
        파생 변수 생성
        """
        # 텍스트 길이 관련
        self.df['text_len'] = self.df['context_cleaned'].str.len()
        self.df['word_count'] = self.df['context_tokenized'].str.split().str.len()
        
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
        self.df['weekday_num'] = self.df['date'].dt.dayofweek
        self.df['year_month'] = self.df['date'].dt.to_period('M').astype(str)
        
        # 텍스트 특성
        emoji_pattern = re.compile(
            "["
            "\U0001F600-\U0001F64F"
            "\U0001F300-\U0001F5FF"
            "\U0001F680-\U0001F6FF"
            "\U0001F1E0-\U0001F1FF"
            "\U00002702-\U000027B0"
            "\U000024C2-\U0001F251"
            "]+", flags=re.UNICODE
        )
        self.df['text_has_emoji'] = self.df['context_cleaned'].apply(
            lambda x: 1 if emoji_pattern.search(str(x)) else 0
        )
        
        url_pattern = re.compile(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+')
        self.df['text_has_url'] = self.df['context_cleaned'].apply(
            lambda x: 1 if url_pattern.search(str(x)) else 0
        )
        
        print("  - 파생 변수 생성 완료")
    
    def _vectorize_text(self):
        """
        텍스트 벡터화 (한글 지원)
        - TF-IDF 벡터화 수행
        - 한글 불용어 제거
        """
        try:
            from sklearn.feature_extraction.text import TfidfVectorizer
            from sklearn.decomposition import TruncatedSVD
            
            # 언어 감지
            languages = self.df['context_cleaned'].apply(detect_language)
            is_korean = languages == 'korean'
            
            # 한글 불용어 가져오기
            korean_stopwords = get_korean_stopwords()
            
            # TF-IDF 벡터화
            print("  - TF-IDF 벡터화 수행 중...")
            tfidf = TfidfVectorizer(
                max_features=100,
                stop_words=None,  # 커스텀 불용어 사용
                ngram_range=(1, 2),
                min_df=2,
                max_df=0.95,
                tokenizer=None,  # 이미 토큰화된 텍스트 사용
                analyzer='word'
            )
            
            # 형태소 분석된 텍스트 사용
            tfidf_matrix = tfidf.fit_transform(self.df['context_tokenized'])
            
            # 차원 축소
            print("  - 차원 축소 수행 중...")
            svd = TruncatedSVD(n_components=20, random_state=42)
            text_vectors = svd.fit_transform(tfidf_matrix)
            
            # 벡터를 데이터프레임에 추가
            for i in range(text_vectors.shape[1]):
                self.df[f'tfidf_vector_{i+1}'] = text_vectors[:, i]
            
            # 주요 키워드 저장
            feature_names = tfidf.get_feature_names_out()
            self.df['top_keywords'] = self.df['context_tokenized'].apply(
                lambda x: self._extract_top_keywords(x, tfidf, feature_names)
            )
            
            print(f"  - TF-IDF 벡터화 완료: {text_vectors.shape[1]}차원 벡터 생성")
            print(f"  - 주요 키워드 추출 완료")
            
        except ImportError:
            print("  - 경고: sklearn이 설치되지 않아 텍스트 벡터화를 건너뜁니다.")
    
    def _extract_top_keywords(self, text: str, vectorizer, feature_names, top_n: int = 5) -> str:
        """
        텍스트에서 상위 키워드 추출
        """
        try:
            tfidf_scores = vectorizer.transform([text])
            feature_index = tfidf_scores[0, :].nonzero()[1]
            
            if len(feature_index) == 0:
                return ""
            
            scores = [(feature_names[i], tfidf_scores[0, i]) for i in feature_index]
            scores.sort(key=lambda x: x[1], reverse=True)
            
            top_keywords = [word for word, score in scores[:top_n]]
            return ', '.join(top_keywords)
        except Exception:
            return ""
    
    def save_to_database(self):
        """
        전처리된 데이터를 database 폴더에 저장
        """
        if self.processed_df is None:
            raise ValueError("전처리된 데이터가 없습니다. preprocess()와 feature_engineering()을 먼저 실행하세요.")
        
        os.makedirs(self.output_dir, exist_ok=True)
        output_path = os.path.join(self.output_dir, 'preprocessed_reviews_google.csv')
        
        # context_tokenized는 저장하지 않고 context_cleaned만 저장
        save_df = self.processed_df.drop(columns=['context_tokenized'], errors='ignore')
        save_df.to_csv(output_path, index=False, encoding='utf-8-sig')
        
        print(f"\n[저장 완료]")
        print(f"  - 저장 경로: {output_path}")
        print(f"  - 데이터 행 수: {len(save_df)}")
        print(f"  - 데이터 열 수: {len(save_df.columns)}")
