"""
EDA 및 시각화 모듈
개별 사이트에 대한 탐색적 데이터 분석 및 시각화를 수행합니다.
"""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
import os
from datetime import datetime
import platform

# 운영체제 확인 후 한글폰트 설정
if platform.system() == 'Windows':
    plt.rc('font', family='Malgun Gothic')
elif platform.system() == 'Darwin': # Mac
    plt.rc('font', family='AppleGothic')
elif platform.system() == 'Linux': # Linux
    # 리눅스는 나눔고딕(NanumGothic)이 기본적으로 많이 쓰입니다.
    plt.rc('font', family='NanumGothic')

# 마이너스 기호 깨짐 방지
plt.rcParams['axes.unicode_minus'] = False


def load_data(csv_path: str) -> pd.DataFrame:
    """CSV 파일 로드"""
    return pd.read_csv(csv_path)


def create_plots_dir(output_dir: str = "review_analysis/plots"):
    """plots 디렉토리 생성"""
    os.makedirs(output_dir, exist_ok=True)
    return output_dir


def plot_rating_distribution(df: pd.DataFrame, site_name: str, output_dir: str):
    """
    별점 분포 시각화
    - 히스토그램
    - 박스플롯
    - 파이차트
    """
    fig, axes = plt.subplots(1, 3, figsize=(18, 5))
    
    # 히스토그램
    axes[0].hist(df['rating'], bins=20, edgecolor='black', alpha=0.7, color='skyblue')
    axes[0].set_xlabel('별점', fontsize=12)
    axes[0].set_ylabel('빈도', fontsize=12)
    axes[0].set_title(f'{site_name} - 별점 분포 (히스토그램)', fontsize=14, fontweight='bold')
    axes[0].grid(True, alpha=0.3)
    
    # 박스플롯
    axes[1].boxplot(df['rating'], vert=True)
    axes[1].set_ylabel('별점', fontsize=12)
    axes[1].set_title(f'{site_name} - 별점 분포 (박스플롯)', fontsize=14, fontweight='bold')
    axes[1].grid(True, alpha=0.3)
    
    # 파이차트
    rating_counts = df['rating'].value_counts().sort_index()
    axes[2].pie(rating_counts.values, labels=rating_counts.index, autopct='%1.1f%%', startangle=90)
    axes[2].set_title(f'{site_name} - 별점 분포 (파이차트)', fontsize=14, fontweight='bold')
    
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, f'{site_name}_rating_distribution.png'), dpi=300, bbox_inches='tight')
    plt.close()
    print(f"  - 별점 분포 그래프 저장: {site_name}_rating_distribution.png")


def plot_text_length_distribution(df: pd.DataFrame, site_name: str, output_dir: str):
    """
    텍스트 길이 분포 시각화
    """
    fig, axes = plt.subplots(1, 2, figsize=(15, 5))
    
    # 컬럼명 확인 (content 또는 text)
    text_col = 'content' if 'content' in df.columns else 'text'
    
    # 문자 수 분포
    axes[0].hist(df[text_col].str.len(), bins=50, edgecolor='black', alpha=0.7, color='lightcoral')
    axes[0].set_xlabel('텍스트 길이 (문자 수)', fontsize=12)
    axes[0].set_ylabel('빈도', fontsize=12)
    axes[0].set_title(f'{site_name} - 텍스트 길이 분포 (문자 수)', fontsize=14, fontweight='bold')
    axes[0].grid(True, alpha=0.3)
    
    # 단어 수 분포
    word_counts = df[text_col].str.split().str.len()
    axes[1].hist(word_counts, bins=50, edgecolor='black', alpha=0.7, color='lightgreen')
    axes[1].set_xlabel('텍스트 길이 (단어 수)', fontsize=12)
    axes[1].set_ylabel('빈도', fontsize=12)
    axes[1].set_title(f'{site_name} - 텍스트 길이 분포 (단어 수)', fontsize=14, fontweight='bold')
    axes[1].grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, f'{site_name}_text_length_distribution.png'), dpi=300, bbox_inches='tight')
    plt.close()
    print(f"  - 텍스트 길이 분포 그래프 저장: {site_name}_text_length_distribution.png")


def plot_date_distribution(df: pd.DataFrame, site_name: str, output_dir: str):
    """
    날짜 분포 시각화
    """
    # 날짜 파싱
    if site_name == "tripcom":
        # Trip.com은 영문 포맷
        date_format = '%b %d, %Y'
    else:
        # 구글, 카카오는 한국식 숫자 포맷
        date_format = '%Y.%m.%d.'

    df['date_parsed'] = pd.to_datetime(df['date'], errors='coerce', format=date_format)
    df_with_date = df.dropna(subset=['date_parsed'])
    
    if len(df_with_date) == 0:
        print(f"  - 경고: {site_name}의 날짜 데이터를 파싱할 수 없습니다.")
        return
    
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    
    # 연도별 리뷰 개수
    df_with_date['year'] = df_with_date['date_parsed'].dt.year
    year_counts = df_with_date['year'].value_counts().sort_index()
    axes[0, 0].bar(year_counts.index, year_counts.values, color='steelblue', alpha=0.7)
    axes[0, 0].set_xlabel('연도', fontsize=12)
    axes[0, 0].set_ylabel('리뷰 개수', fontsize=12)
    axes[0, 0].set_title(f'{site_name} - 연도별 리뷰 개수', fontsize=14, fontweight='bold')
    axes[0, 0].grid(True, alpha=0.3, axis='y')
    axes[0, 0].tick_params(axis='x', rotation=45)
    
    # 월별 리뷰 개수
    df_with_date['month'] = df_with_date['date_parsed'].dt.month
    month_counts = df_with_date['month'].value_counts().sort_index()
    axes[0, 1].bar(month_counts.index, month_counts.values, color='coral', alpha=0.7)
    axes[0, 1].set_xlabel('월', fontsize=12)
    axes[0, 1].set_ylabel('리뷰 개수', fontsize=12)
    axes[0, 1].set_title(f'{site_name} - 월별 리뷰 개수', fontsize=14, fontweight='bold')
    axes[0, 1].grid(True, alpha=0.3, axis='y')
    
    # 요일별 리뷰 개수
    df_with_date['weekday'] = df_with_date['date_parsed'].dt.day_name()
    weekday_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    weekday_counts = df_with_date['weekday'].value_counts()
    weekday_counts = weekday_counts.reindex([w for w in weekday_order if w in weekday_counts.index])
    axes[1, 0].bar(range(len(weekday_counts)), weekday_counts.values, color='mediumseagreen', alpha=0.7)
    axes[1, 0].set_xticks(range(len(weekday_counts)))
    axes[1, 0].set_xticklabels(weekday_counts.index, rotation=45, ha='right')
    axes[1, 0].set_xlabel('요일', fontsize=12)
    axes[1, 0].set_ylabel('리뷰 개수', fontsize=12)
    axes[1, 0].set_title(f'{site_name} - 요일별 리뷰 개수', fontsize=14, fontweight='bold')
    axes[1, 0].grid(True, alpha=0.3, axis='y')
    
    # 시계열 추이 (연도-월별)
    df_with_date['year_month'] = df_with_date['date_parsed'].dt.to_period('M')
    time_series = df_with_date['year_month'].value_counts().sort_index()
    axes[1, 1].plot(range(len(time_series)), time_series.values, marker='o', linewidth=2, markersize=4)
    axes[1, 1].set_xticks(range(0, len(time_series), max(1, len(time_series)//10)))
    axes[1, 1].set_xticklabels([str(time_series.index[i]) for i in range(0, len(time_series), max(1, len(time_series)//10))], 
                                rotation=45, ha='right')
    axes[1, 1].set_xlabel('연도-월', fontsize=12)
    axes[1, 1].set_ylabel('리뷰 개수', fontsize=12)
    axes[1, 1].set_title(f'{site_name} - 시계열 리뷰 추이', fontsize=14, fontweight='bold')
    axes[1, 1].grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, f'{site_name}_date_distribution.png'), dpi=300, bbox_inches='tight')
    plt.close()
    print(f"  - 날짜 분포 그래프 저장: {site_name}_date_distribution.png")


def plot_correlation_analysis(df: pd.DataFrame, site_name: str, output_dir: str):
    """
    상관관계 분석 시각화
    """
    # 컬럼명 확인
    text_col = 'content' if 'content' in df.columns else 'text'
    
    fig, axes = plt.subplots(1, 2, figsize=(15, 5))
    
    # 별점 vs 텍스트 길이 (문자 수)
    text_lengths = df[text_col].str.len()
    axes[0].scatter(text_lengths, df['rating'], alpha=0.5, s=20)
    axes[0].set_xlabel('텍스트 길이 (문자 수)', fontsize=12)
    axes[0].set_ylabel('별점', fontsize=12)
    axes[0].set_title(f'{site_name} - 별점 vs 텍스트 길이 (문자 수)', fontsize=14, fontweight='bold')
    axes[0].grid(True, alpha=0.3)
    
    # 별점 vs 텍스트 길이 (단어 수)
    word_counts = df[text_col].str.split().str.len()
    axes[1].scatter(word_counts, df['rating'], alpha=0.5, s=20, color='coral')
    axes[1].set_xlabel('텍스트 길이 (단어 수)', fontsize=12)
    axes[1].set_ylabel('별점', fontsize=12)
    axes[1].set_title(f'{site_name} - 별점 vs 텍스트 길이 (단어 수)', fontsize=14, fontweight='bold')
    axes[1].grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, f'{site_name}_correlation_analysis.png'), dpi=300, bbox_inches='tight')
    plt.close()
    print(f"  - 상관관계 분석 그래프 저장: {site_name}_correlation_analysis.png")


def perform_eda_for_site(csv_path: str, site_name: str, output_dir: str = "review_analysis/plots"):
    """
    특정 사이트에 대한 전체 EDA 수행
    """
    print(f"\n[{site_name}] EDA 수행 중...")
    
    # 데이터 로드
    df = load_data(csv_path)
    print(f"  - 데이터 로드 완료: {len(df)} rows, {len(df.columns)} columns")
    
    # plots 디렉토리 생성
    plots_dir = create_plots_dir(output_dir)
    
    # 각종 시각화 수행
    plot_rating_distribution(df, site_name, plots_dir)
    plot_text_length_distribution(df, site_name, plots_dir)
    plot_date_distribution(df, site_name, plots_dir)
    plot_correlation_analysis(df, site_name, plots_dir)
    
    print(f"[{site_name}] EDA 완료!\n")
