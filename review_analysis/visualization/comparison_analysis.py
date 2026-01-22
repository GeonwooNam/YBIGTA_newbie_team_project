"""
비교 분석 및 시각화 모듈
여러 사이트 간 텍스트 비교 분석 및 시계열 분석을 수행합니다.
"""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
import os
from collections import Counter
from datetime import datetime
import glob

# 한글 폰트 설정
plt.rcParams['font.family'] = 'Malgun Gothic'  # Windows
plt.rcParams['axes.unicode_minus'] = False

try:
    plt.rcParams['font.family'] = 'Malgun Gothic'
except:
    try:
        plt.rcParams['font.family'] = 'AppleGothic'  # Mac
    except:
        plt.rcParams['font.family'] = 'DejaVu Sans'


def load_preprocessed_data(csv_path: str) -> pd.DataFrame:
    """전처리된 CSV 파일 로드"""
    return pd.read_csv(csv_path)


def plot_keyword_comparison(data_dict: dict, output_dir: str):
    """
    사이트별 키워드 빈도 비교
    """
    # 각 사이트의 상위 키워드 추출
    all_keywords = {}
    for site_name, df in data_dict.items():
        if 'top_keywords' in df.columns:
            keywords_list = []
            for keywords_str in df['top_keywords'].dropna():
                if pd.notna(keywords_str) and keywords_str:
                    keywords_list.extend([k.strip() for k in str(keywords_str).split(',')])
            keyword_counts = Counter(keywords_list)
            all_keywords[site_name] = keyword_counts.most_common(20)  # 상위 20개
    
    if not all_keywords:
        print("  - 경고: 키워드 데이터가 없어 키워드 비교를 건너뜁니다.")
        return
    
    # 시각화
    n_sites = len(all_keywords)
    fig, axes = plt.subplots(1, n_sites, figsize=(8*n_sites, 6))
    if n_sites == 1:
        axes = [axes]
    
    for idx, (site_name, top_keywords) in enumerate(all_keywords.items()):
        if top_keywords:
            keywords, counts = zip(*top_keywords)
            axes[idx].barh(range(len(keywords)), counts, color='steelblue', alpha=0.7)
            axes[idx].set_yticks(range(len(keywords)))
            axes[idx].set_yticklabels(keywords)
            axes[idx].set_xlabel('빈도', fontsize=12)
            axes[idx].set_title(f'{site_name} - 상위 키워드', fontsize=14, fontweight='bold')
            axes[idx].invert_yaxis()
            axes[idx].grid(True, alpha=0.3, axis='x')
    
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'keyword_comparison.png'), dpi=300, bbox_inches='tight')
    plt.close()
    print(f"  - 키워드 비교 그래프 저장: keyword_comparison.png")


def plot_rating_comparison(data_dict: dict, output_dir: str):
    """
    사이트별 별점 분포 비교
    """
    fig, axes = plt.subplots(1, 2, figsize=(16, 6))
    
    # 박스플롯 비교
    box_data = []
    box_labels = []
    for site_name, df in data_dict.items():
        box_data.append(df['rating'].values)
        box_labels.append(site_name)
    
    axes[0].boxplot(box_data, labels=box_labels)
    axes[0].set_ylabel('별점', fontsize=12)
    axes[0].set_title('사이트별 별점 분포 비교 (박스플롯)', fontsize=14, fontweight='bold')
    axes[0].grid(True, alpha=0.3, axis='y')
    
    # 히스토그램 비교
    for site_name, df in data_dict.items():
        axes[1].hist(df['rating'], bins=20, alpha=0.6, label=site_name, edgecolor='black')
    axes[1].set_xlabel('별점', fontsize=12)
    axes[1].set_ylabel('빈도', fontsize=12)
    axes[1].set_title('사이트별 별점 분포 비교 (히스토그램)', fontsize=14, fontweight='bold')
    axes[1].legend()
    axes[1].grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'rating_comparison.png'), dpi=300, bbox_inches='tight')
    plt.close()
    print(f"  - 별점 비교 그래프 저장: rating_comparison.png")


def plot_text_length_comparison(data_dict: dict, output_dir: str):
    """
    사이트별 텍스트 길이 비교
    """
    fig, axes = plt.subplots(1, 2, figsize=(16, 6))
    
    # 문자 수 비교
    for site_name, df in data_dict.items():
        if 'text_len' in df.columns:
            axes[0].hist(df['text_len'], bins=50, alpha=0.6, label=site_name, edgecolor='black')
        else:
            text_col = 'context' if 'context' in df.columns else 'text'
            text_lengths = df[text_col].str.len()
            axes[0].hist(text_lengths, bins=50, alpha=0.6, label=site_name, edgecolor='black')
    
    axes[0].set_xlabel('텍스트 길이 (문자 수)', fontsize=12)
    axes[0].set_ylabel('빈도', fontsize=12)
    axes[0].set_title('사이트별 텍스트 길이 비교 (문자 수)', fontsize=14, fontweight='bold')
    axes[0].legend()
    axes[0].grid(True, alpha=0.3)
    
    # 단어 수 비교
    for site_name, df in data_dict.items():
        if 'word_count' in df.columns:
            axes[1].hist(df['word_count'], bins=50, alpha=0.6, label=site_name, edgecolor='black')
        else:
            text_col = 'context' if 'context' in df.columns else 'text'
            word_counts = df[text_col].str.split().str.len()
            axes[1].hist(word_counts, bins=50, alpha=0.6, label=site_name, edgecolor='black')
    
    axes[1].set_xlabel('텍스트 길이 (단어 수)', fontsize=12)
    axes[1].set_ylabel('빈도', fontsize=12)
    axes[1].set_title('사이트별 텍스트 길이 비교 (단어 수)', fontsize=14, fontweight='bold')
    axes[1].legend()
    axes[1].grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'text_length_comparison.png'), dpi=300, bbox_inches='tight')
    plt.close()
    print(f"  - 텍스트 길이 비교 그래프 저장: text_length_comparison.png")


def plot_timeseries_comparison(data_dict: dict, output_dir: str):
    """
    사이트별 시계열 비교 (연도-월별 리뷰 개수 추이)
    """
    fig, ax = plt.subplots(1, 1, figsize=(16, 6))
    
    for site_name, df in data_dict.items():
        # 날짜 파싱
        if 'year_month' in df.columns:
            time_series = df['year_month'].value_counts().sort_index()
        else:
            df['date_parsed'] = pd.to_datetime(df['date'], errors='coerce', format='%b %d, %Y')
            df_with_date = df.dropna(subset=['date_parsed'])
            if len(df_with_date) > 0:
                df_with_date['year_month'] = df_with_date['date_parsed'].dt.to_period('M')
                time_series = df_with_date['year_month'].value_counts().sort_index()
            else:
                continue
        
        # 시계열 플롯
        time_labels = [str(t) for t in time_series.index]
        ax.plot(range(len(time_series)), time_series.values, marker='o', label=site_name, linewidth=2, markersize=4)
    
    ax.set_xlabel('연도-월', fontsize=12)
    ax.set_ylabel('리뷰 개수', fontsize=12)
    ax.set_title('사이트별 시계열 리뷰 추이 비교', fontsize=14, fontweight='bold')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    # x축 레이블 설정 (일부만 표시)
    if len(time_labels) > 0:
        step = max(1, len(time_labels) // 10)
        ax.set_xticks(range(0, len(time_labels), step))
        ax.set_xticklabels([time_labels[i] for i in range(0, len(time_labels), step)], rotation=45, ha='right')
    
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'timeseries_comparison.png'), dpi=300, bbox_inches='tight')
    plt.close()
    print(f"  - 시계열 비교 그래프 저장: timeseries_comparison.png")


def plot_rating_group_comparison(data_dict: dict, output_dir: str):
    """
    사이트별 별점 그룹 비교
    """
    if not all('rating_group' in df.columns for df in data_dict.values()):
        return
    
    fig, ax = plt.subplots(1, 1, figsize=(12, 6))
    
    # 데이터 준비
    comparison_data = []
    for site_name, df in data_dict.items():
        rating_groups = df['rating_group'].value_counts()
        for group, count in rating_groups.items():
            comparison_data.append({
                'Site': site_name,
                'Rating Group': str(group),
                'Count': count
            })
    
    comparison_df = pd.DataFrame(comparison_data)
    
    # 막대 그래프
    comparison_df_pivot = comparison_df.pivot(index='Rating Group', columns='Site', values='Count')
    comparison_df_pivot.plot(kind='bar', ax=ax, width=0.8, alpha=0.8)
    
    ax.set_xlabel('별점 그룹', fontsize=12)
    ax.set_ylabel('리뷰 개수', fontsize=12)
    ax.set_title('사이트별 별점 그룹 비교', fontsize=14, fontweight='bold')
    ax.legend(title='사이트')
    ax.grid(True, alpha=0.3, axis='y')
    ax.tick_params(axis='x', rotation=0)
    
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'rating_group_comparison.png'), dpi=300, bbox_inches='tight')
    plt.close()
    print(f"  - 별점 그룹 비교 그래프 저장: rating_group_comparison.png")


def perform_comparison_analysis(database_dir: str = "../../database", output_dir: str = "review_analysis/plots"):
    """
    모든 전처리된 데이터에 대한 비교 분석 수행
    """
    print("\n[비교 분석] 수행 중...")
    
    # 전처리된 CSV 파일 찾기
    preprocessed_files = glob.glob(os.path.join(database_dir, "preprocessed_reviews_*.csv"))
    
    if len(preprocessed_files) == 0:
        print("  - 경고: 전처리된 데이터 파일을 찾을 수 없습니다.")
        return
    
    # 데이터 로드
    data_dict = {}
    for file_path in preprocessed_files:
        site_name = os.path.basename(file_path).replace('preprocessed_reviews_', '').replace('.csv', '')
        df = load_preprocessed_data(file_path)
        data_dict[site_name] = df
        print(f"  - {site_name} 데이터 로드: {len(df)} rows")
    
    if len(data_dict) == 0:
        print("  - 경고: 비교할 데이터가 없습니다.")
        return
    
    # plots 디렉토리 생성
    os.makedirs(output_dir, exist_ok=True)
    
    # 각종 비교 시각화 수행
    plot_rating_comparison(data_dict, output_dir)
    plot_text_length_comparison(data_dict, output_dir)
    plot_timeseries_comparison(data_dict, output_dir)
    plot_keyword_comparison(data_dict, output_dir)
    plot_rating_group_comparison(data_dict, output_dir)
    
    print("[비교 분석] 완료!\n")
