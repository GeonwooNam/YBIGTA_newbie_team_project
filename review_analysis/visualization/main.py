"""
시각화 메인 실행 스크립트
"""
import os
import sys
import glob
from pathlib import Path

# 프로젝트 루트를 경로에 추가
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from review_analysis.visualization.eda_analysis import perform_eda_for_site
from review_analysis.visualization.comparison_analysis import perform_comparison_analysis
from review_analysis.visualization.sentiment_analysis import perform_sentiment_analysis_for_site


def main():
    """메인 실행 함수"""
    # 경로 설정
    database_dir = os.path.join(project_root, "database")
    plots_dir = os.path.join(project_root, "review_analysis", "plots")
    
    # plots 디렉토리 생성
    os.makedirs(plots_dir, exist_ok=True)
    
    print("=" * 60)
    print("EDA 및 비교 분석 시각화 시작")
    print("=" * 60)
    
    # 1. 원본 데이터에 대한 EDA
    print("\n[1단계] 원본 데이터 EDA 수행")
    original_files = glob.glob(os.path.join(database_dir, "reviews_*.csv"))
    for file_path in original_files:
        site_name = os.path.basename(file_path).replace('reviews_', '').replace('.csv', '')
        perform_eda_for_site(file_path, site_name, plots_dir)
    
    # 2. 감정 분석 및 단어-별점 상관관계 분석
    print("\n[2단계] 감정 분석 및 단어-별점 상관관계 분석 수행")
    for file_path in original_files:
        site_name = os.path.basename(file_path).replace('reviews_', '').replace('.csv', '')
        perform_sentiment_analysis_for_site(file_path, site_name, plots_dir)
    
    # 3. 전처리된 데이터에 대한 비교 분석
    print("\n[3단계] 전처리된 데이터 비교 분석 수행")
    perform_comparison_analysis(database_dir, plots_dir)
    
    print("=" * 60)
    print("모든 시각화 완료!")
    print(f"결과는 {plots_dir} 폴더에 저장되었습니다.")
    print("=" * 60)


if __name__ == "__main__":
    main()
