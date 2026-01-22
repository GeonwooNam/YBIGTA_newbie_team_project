import os
import sys
import glob
from argparse import ArgumentParser
from typing import Dict, Type

# 프로젝트 루트를 경로에 추가 (preprocessing 폴더에서 실행할 때를 위해)
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.join(current_dir, '..', '..')
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from review_analysis.preprocessing.base_processor import BaseDataProcessor
from review_analysis.preprocessing.example_processor import ExampleProcessor
from review_analysis.preprocessing.tripcom_processor import TripComProcessor
from review_analysis.preprocessing.google_processor import GoogleProcessor
from review_analysis.preprocessing.kakao_processor import KakaoProcessor


# 모든 preprocessing 클래스를 예시 형식으로 적어주세요. 
# key는 "reviews_사이트이름"으로, value는 해당 처리를 위한 클래스
PREPROCESS_CLASSES: Dict[str, Type[BaseDataProcessor]] = {
    # "reviews_example": ExampleProcessor,
    "reviews_tripcom": TripComProcessor,
    "reviews_google": GoogleProcessor,
    "reviews_kakao": KakaoProcessor,
    # key는 크롤링한 csv파일 이름으로 적어주세요! ex. reviews_naver.csv -> reviews_naver
}

REVIEW_COLLECTIONS = glob.glob(os.path.join("..","..","database", "reviews_*.csv"))

def create_parser() -> ArgumentParser:
    parser = ArgumentParser()
    parser.add_argument('-o', '--output_dir', type=str, required=False, default = "../../database", help="Output file dir. Example: ../../database")
    parser.add_argument('-c', '--preprocessor', type=str, required=False, choices=PREPROCESS_CLASSES.keys(),
                        help=f"Which processor to use. Choices: {', '.join(PREPROCESS_CLASSES.keys())}")
    parser.add_argument('-a', '--all', action='store_true',
                        help="Run all data preprocessors. Default to False.")    
    return parser

if __name__ == "__main__":

    parser = create_parser()
    args = parser.parse_args()

    os.makedirs(args.output_dir, exist_ok=True)

    if args.all: 
        for csv_file in REVIEW_COLLECTIONS:
            base_name = os.path.splitext(os.path.basename(csv_file))[0]
            if base_name in PREPROCESS_CLASSES:
                preprocessor_class = PREPROCESS_CLASSES[base_name]
                preprocessor = preprocessor_class(csv_file, args.output_dir)
                preprocessor.preprocess()
                preprocessor.feature_engineering()
                preprocessor.save_to_database()
