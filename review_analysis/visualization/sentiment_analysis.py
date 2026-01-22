"""
감정 분석 및 단어-별점 상관관계 분석 모듈
"""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
from collections import Counter, defaultdict
import re
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


# 간단한 긍정/부정 단어 사전
POSITIVE_WORDS = {
    'good', 'great', 'excellent', 'amazing', 'wonderful', 'fantastic', 'awesome',
    'love', 'loved', 'enjoy', 'enjoyed', 'perfect', 'best', 'beautiful', 'nice',
    'fun', 'happy', 'satisfied', 'recommend', 'impressive', 'outstanding',
    'delightful', 'pleased', 'brilliant', 'superb', 'marvelous', 'fabulous',
    'terrific', 'exceptional', 'incredible', 'wonderful', 'pleasant', 'charming'
}

NEGATIVE_WORDS = {
    'bad', 'terrible', 'awful', 'horrible', 'worst', 'disappointed', 'disappointing',
    'poor', 'hate', 'hated', 'boring', 'waste', 'wasted', 'regret', 'regretted',
    'disgusting', 'annoying', 'frustrated', 'frustrating', 'unhappy', 'sad',
    'angry', 'upset', 'disappointed', 'disgusted', 'awful', 'horrible', 'terrible',
    'worst', 'poor', 'bad', 'unpleasant', 'disappointing', 'unsatisfied'
}


def calculate_sentiment_score(text: str) -> float:
    """
    간단한 감정 점수 계산 (긍정 단어 - 부정 단어)
    """
    if pd.isna(text):
        return 0.0
    
    text = str(text).lower()
    words = re.findall(r'\b\w+\b', text)
    
    positive_count = sum(1 for word in words if word in POSITIVE_WORDS)
    negative_count = sum(1 for word in words if word in NEGATIVE_WORDS)
    
    # 정규화 (단어 수로 나눔)
    total_words = len(words)
    if total_words == 0:
        return 0.0
    
    sentiment_score = (positive_count - negative_count) / total_words * 100
    return sentiment_score


def analyze_word_rating_correlation(df: pd.DataFrame, text_col: str = 'content', top_n: int = 20):
    """
    단어별 평균 별점 분석
    """
    word_ratings = defaultdict(list)
    
    for idx, row in df.iterrows():
        text = str(row[text_col]).lower()
        rating = row['rating']
        
        # 단어 추출 (영문자만, 최소 3글자)
        words = re.findall(r'\b[a-z]{3,}\b', text)
        
        for word in words:
            word_ratings[word].append(rating)
    
    # 평균 별점 계산
    word_avg_ratings = {}
    for word, ratings in word_ratings.items():
        if len(ratings) >= 3:  # 최소 3번 이상 등장한 단어만
            word_avg_ratings[word] = {
                'avg_rating': np.mean(ratings),
                'count': len(ratings),
                'std': np.std(ratings)
            }
    
    # 평균 별점 기준으로 정렬
    sorted_words = sorted(word_avg_ratings.items(), key=lambda x: x[1]['avg_rating'], reverse=True)
    
    return sorted_words[:top_n], sorted_words[-top_n:]


def plot_word_rating_correlation(df: pd.DataFrame, site_name: str, output_dir: str, text_col: str = 'content'):
    """
    단어별 평균 별점 시각화
    """
    print("  - 단어-별점 상관관계 분석 중...")
    
    top_positive_words, top_negative_words = analyze_word_rating_correlation(df, text_col, top_n=15)
    
    fig, axes = plt.subplots(1, 2, figsize=(18, 8))
    
    # 상위 긍정 단어 (높은 평균 별점)
    if top_positive_words:
        words = [w[0] for w in top_positive_words]
        avg_ratings = [w[1]['avg_rating'] for w in top_positive_words]
        counts = [w[1]['count'] for w in top_positive_words]
        
        # 버블 차트 (크기는 등장 횟수)
        scatter = axes[0].scatter(range(len(words)), avg_ratings, s=[c*10 for c in counts], 
                                 alpha=0.6, c=avg_ratings, cmap='RdYlGn', edgecolors='black')
        axes[0].set_xticks(range(len(words)))
        axes[0].set_xticklabels(words, rotation=45, ha='right')
        axes[0].set_ylabel('평균 별점', fontsize=12)
        axes[0].set_title(f'{site_name} - 높은 별점과 연관된 단어 (Top 15)', fontsize=14, fontweight='bold')
        axes[0].grid(True, alpha=0.3, axis='y')
        axes[0].set_ylim([0, 5.5])
        plt.colorbar(scatter, ax=axes[0], label='평균 별점')
    
    # 하위 부정 단어 (낮은 평균 별점)
    if top_negative_words:
        words = [w[0] for w in top_negative_words]
        avg_ratings = [w[1]['avg_rating'] for w in top_negative_words]
        counts = [w[1]['count'] for w in top_negative_words]
        
        scatter = axes[1].scatter(range(len(words)), avg_ratings, s=[c*10 for c in counts], 
                                 alpha=0.6, c=avg_ratings, cmap='RdYlGn_r', edgecolors='black')
        axes[1].set_xticks(range(len(words)))
        axes[1].set_xticklabels(words, rotation=45, ha='right')
        axes[1].set_ylabel('평균 별점', fontsize=12)
        axes[1].set_title(f'{site_name} - 낮은 별점과 연관된 단어 (Bottom 15)', fontsize=14, fontweight='bold')
        axes[1].grid(True, alpha=0.3, axis='y')
        axes[1].set_ylim([0, 5.5])
        plt.colorbar(scatter, ax=axes[1], label='평균 별점')
    
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, f'{site_name}_word_rating_correlation.png'), dpi=300, bbox_inches='tight')
    plt.close()
    print(f"  - 단어-별점 상관관계 그래프 저장: {site_name}_word_rating_correlation.png")


def plot_sentiment_rating_correlation(df: pd.DataFrame, site_name: str, output_dir: str, text_col: str = 'content'):
    """
    감정 점수와 별점의 상관관계 시각화
    """
    print("  - 감정 점수 계산 중...")
    
    # 감정 점수 계산
    df['sentiment_score'] = df[text_col].apply(calculate_sentiment_score)
    
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    
    # 1. 감정 점수 vs 별점 산점도
    axes[0, 0].scatter(df['sentiment_score'], df['rating'], alpha=0.5, s=20)
    axes[0, 0].set_xlabel('감정 점수 (긍정 단어 - 부정 단어)', fontsize=12)
    axes[0, 0].set_ylabel('별점', fontsize=12)
    axes[0, 0].set_title(f'{site_name} - 감정 점수 vs 별점', fontsize=14, fontweight='bold')
    axes[0, 0].grid(True, alpha=0.3)
    
    # 상관계수 계산
    correlation = df['sentiment_score'].corr(df['rating'])
    axes[0, 0].text(0.05, 0.95, f'상관계수: {correlation:.3f}', 
                    transform=axes[0, 0].transAxes, fontsize=12,
                    verticalalignment='top', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
    
    # 2. 감정 점수 분포
    axes[0, 1].hist(df['sentiment_score'], bins=30, edgecolor='black', alpha=0.7, color='skyblue')
    axes[0, 1].set_xlabel('감정 점수', fontsize=12)
    axes[0, 1].set_ylabel('빈도', fontsize=12)
    axes[0, 1].set_title(f'{site_name} - 감정 점수 분포', fontsize=14, fontweight='bold')
    axes[0, 1].axvline(x=0, color='red', linestyle='--', linewidth=2, label='중립 (0)')
    axes[0, 1].legend()
    axes[0, 1].grid(True, alpha=0.3)
    
    # 3. 감정 점수 구간별 평균 별점
    df['sentiment_category'] = pd.cut(df['sentiment_score'], 
                                       bins=[-np.inf, -5, 0, 5, np.inf],
                                       labels=['부정적', '약간 부정적', '약간 긍정적', '긍정적'])
    sentiment_rating = df.groupby('sentiment_category', observed=True)['rating'].mean()
    
    axes[1, 0].bar(range(len(sentiment_rating)), sentiment_rating.values, 
                   color=['red', 'orange', 'lightgreen', 'green'], alpha=0.7, edgecolor='black')
    axes[1, 0].set_xticks(range(len(sentiment_rating)))
    axes[1, 0].set_xticklabels(sentiment_rating.index, rotation=0)
    axes[1, 0].set_ylabel('평균 별점', fontsize=12)
    axes[1, 0].set_title(f'{site_name} - 감정 카테고리별 평균 별점', fontsize=14, fontweight='bold')
    axes[1, 0].grid(True, alpha=0.3, axis='y')
    axes[1, 0].set_ylim([0, 5.5])
    
    # 4. 감정 점수 구간별 리뷰 개수
    sentiment_counts = df['sentiment_category'].value_counts().sort_index()
    axes[1, 1].bar(range(len(sentiment_counts)), sentiment_counts.values,
                   color=['red', 'orange', 'lightgreen', 'green'], alpha=0.7, edgecolor='black')
    axes[1, 1].set_xticks(range(len(sentiment_counts)))
    axes[1, 1].set_xticklabels(sentiment_counts.index, rotation=0)
    axes[1, 1].set_ylabel('리뷰 개수', fontsize=12)
    axes[1, 1].set_title(f'{site_name} - 감정 카테고리별 리뷰 개수', fontsize=14, fontweight='bold')
    axes[1, 1].grid(True, alpha=0.3, axis='y')
    
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, f'{site_name}_sentiment_rating_correlation.png'), dpi=300, bbox_inches='tight')
    plt.close()
    print(f"  - 감정 점수-별점 상관관계 그래프 저장: {site_name}_sentiment_rating_correlation.png")
    
    return df


def perform_sentiment_analysis_for_site(csv_path: str, site_name: str, output_dir: str = "review_analysis/plots"):
    """
    특정 사이트에 대한 감정 분석 수행
    """
    print(f"\n[{site_name}] 감정 분석 수행 중...")
    
    # 데이터 로드
    df = pd.read_csv(csv_path)
    
    # 컬럼명 확인
    text_col = 'content' if 'content' in df.columns else 'text'
    if text_col not in df.columns:
        print(f"  - 경고: {site_name}에 텍스트 컬럼이 없습니다.")
        return
    
    # plots 디렉토리 생성
    os.makedirs(output_dir, exist_ok=True)
    
    # 단어-별점 상관관계 분석
    plot_word_rating_correlation(df, site_name, output_dir, text_col)
    
    # 감정 점수-별점 상관관계 분석
    df_with_sentiment = plot_sentiment_rating_correlation(df, site_name, output_dir, text_col)
    
    print(f"[{site_name}] 감정 분석 완료!\n")
    
    return df_with_sentiment
