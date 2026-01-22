import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from base_processor import BaseDataProcessor


class ReviewDataProcessor(BaseDataProcessor):
    """
    리뷰 데이터의 전처리, 피처 엔지니어링 및 벡터화를 수행하는 클래스입니다.
    BaseDataProcessor를 상속받아 구현되었습니다.

    Attributes:
        input_path (str): 읽어올 원본 CSV 파일 경로
        output_dir (str): 전처리된 결과를 저장할 디렉토리 경로
        df (pd.DataFrame): 프로세싱할 데이터프레임
        vectorizer (TfidfVectorizer): 텍스트 벡터화를 위한 TF-IDF 객체
    """

    def __init__(self, input_path: str, output_dir: str):
        """
        ReviewDataProcessor 클래스의 초기화 메서드입니다.

        Args:
            input_path (str): 입력 파일 경로
            output_dir (str): 결과 파일 저장 경로
        """
        super().__init__(input_path, output_dir)
        self.df = None
        # 최대 1000개의 핵심 단어를 추출하도록 설정된 TF-IDF 벡터라이저
        self.vectorizer = TfidfVectorizer(max_features=1000)

    def preprocess(self):
        """
        원본 데이터의 결측치 처리, 이상치 제거 및 칼럼명 통일을 수행합니다.

        1. 데이터 로드
        2. 날짜 형식 변환 및 유효 기간(2019~2026) 필터링
        3. 텍스트 칼럼명 통일 ('text' -> 'context')
        4. 결측치 처리: 별점은 평균으로 대체, 리뷰와 날짜는 해당 행 삭제
        5. 이상치 처리: 길이가 2자 이하인 의미 없는 짧은 리뷰 제거

        Returns:
            pd.DataFrame: 전처리가 완료된 데이터프레임
        """
        # 1. 데이터 로드 (CSV 파일 가정)
        self.df = pd.read_csv(self.input_path)

        # 2. 날짜 변환 및 기간 필터링 (EDA 결과 반영: 2019~2026년 데이터만 유지)
        self.df['date'] = pd.to_datetime(self.df['date'])
        self.df = self.df[(self.df['date'].dt.year >= 2019) & (self.df['date'].dt.year <= 2026)]

        # 3. 칼럼명 통일 (text 혹은 content -> context)
        # 다양한 소스에서 온 데이터의 분석 편의성을 위해 이름을 'context'로 단일화
        if 'text' in self.df.columns:
            self.df = self.df.rename(columns={'text': 'context'})
        elif 'content' in self.df.columns:
            self.df = self.df.rename(columns={'content': 'context'})

        # 4. 결측치(Missing Values) 처리
        # 별점(rating)은 수치형 데이터이므로 전체 평균으로 대체하여 데이터 손실 최소화
        mean_rating = self.df['rating'].mean()
        self.df['rating'] = self.df['rating'].fillna(mean_rating)

        # 리뷰 내용(context)과 날짜(date)는 분석의 핵심이므로 결측치일 경우 해당 행 삭제
        self.df.dropna(subset=['context', 'date'], inplace=True)

        # 5. 텍스트 클리닝 및 이상치 처리
        # '굿', 'ㅛ', 이모티콘 등 분석 가치가 낮은 2자 이하의 리뷰는 이상치로 판단하여 제거
        self.df = self.df[self.df['context'].str.len() > 2]

        return self.df

    def feature_engineering(self):
        """
        분석에 필요한 파생 변수를 생성합니다.

        생성되는 파생 변수:
        1. text_len: 리뷰 텍스트의 전체 길이
        2. month: 리뷰 작성 월 (계절성 분석용)
        3. weekday: 리뷰 작성 요일 (0: 월요일 ~ 6: 일요일)

        Returns:
            pd.DataFrame: 파생 변수가 추가된 데이터프레임
        """
        # 1. 리뷰 길이: 감성 수치나 리뷰의 성의 정도를 파악하는 지표로 활용
        self.df['text_len'] = self.df['context'].apply(len)

        # 2. 시간 관련 변수 추출: 월별 방문객 흐름 및 평일/주말 방문 특성 비교용
        self.df['month'] = self.df['date'].dt.month
        self.df['weekday'] = self.df['date'].dt.weekday

        return self.df

    def vectorize_text(self):
        """
        전처리된 텍스트 데이터를 TF-IDF 방식을 사용하여 수치형 벡터로 변환합니다.

        Returns:
            scipy.sparse.csr.csr_matrix: 텍스트 데이터의 TF-IDF 벡터 행렬
        """
        # fit_transform을 통해 어휘 사전을 구축하고 동시에 벡터화 진행
        tfidf_matrix = self.vectorizer.fit_transform(self.df['context'])
        return tfidf_matrix

    def save_to_database(self):
        """
        최종적으로 전처리 및 피처 엔지니어링이 완료된 데이터를 CSV 파일로 저장합니다.
        저장 경로는 초기화 시 지정한 output_dir을 기준으로 합니다.
        """
        output_path = f"{self.output_dir}/processed_reviews.csv"
        # 인덱스를 제외하고 저장하여 파일 크기 최적화 및 로드 편의성 증대
        self.df.to_csv(output_path, index=False)
        print(f"데이터 저장 완료: {output_path}")