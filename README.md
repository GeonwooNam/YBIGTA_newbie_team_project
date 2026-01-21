# YBIGTA Newbie Team Project

## 👥 팀 소개

*(추후 작성 예정)* 

---
## 프로젝트 구조 

```text
YBIGTA_newbie_team_project/
├── github/                      # 협업 과제 증빙 이미지
├── database/                    # 데이터 저장 폴더
│   ├── reviews_{사이트}.csv      # 원본 데이터
│   └── preprocessed_reviews_{사이트}.csv # 전처리 완료 데이터
├── review_analysis/
│   ├── crawling/                # 크롤링 소스 코드
│   ├── preprocessing/           # 전처리 소스 코드
│   └── plots/                   # 시각화 그래프 이미지
├── utils/                       # 공통 유틸리티 (logger 등)
├── .gitignore                   # 캐시 파일 관리
├── requirements.txt             # 패키지 의존성
└── README.md                    # 프로젝트 안내서

```

---

## 3-2. 크롤링 과제 

1) 데이터 소개 

본 프로젝트는 **에버랜드** 를 대상으로 다양한 사이트의 리뷰 데이터를 수집하였습니다.

| 사이트 | 링크 | 수집 개수 |
| --- | --- | --- |
| **Trip.com** | [링크](https://us.trip.com/review/everland-10558712-244874246?locale=en-US&curr=KRW) | 488개
| **Google Maps** | [링크](https://www.google.com/maps) | 500개
| **Kakao Map** | [링크](https://place.map.kakao.com/784414359#review) | 500개 

* **데이터 형식**: CSV (UTF-8 with BOM) 


* **저장 위치**: `database/reviews_{사이트이름}.csv` 



2) 실행 방법 

```bash
# 1. 환경 설정
pip install -r requirements.txt

# 2. 모든 크롤러 실행 (명세 기준)
python main.py -o database --all

# 3. 특정 크롤러만 실행 (예: tripcom)
python main.py -o database -c tripcom

```

---

## 4-1. EDA & FE, 시각화 과제 

1) EDA 및 시각화 

각 사이트별 리뷰 데이터의 특성과 분포를 시각화하여 분석하였습니다. 상세 그래프는 `review_analysis/plots/` 폴더에서 확인 가능합니다.

* **분포 파악**: 별점, 텍스트 길이, 날짜별 리뷰 분포 시각화 


* **이상치 파악**: 별점 범위를 벗어난 값 또는 비정상적인 기간의 데이터 분석 



2) 전처리 및 FE (Feature Engineering) 

`BaseDataProcessor`를 상속받아 아래 작업을 수행하였습니다.

* **결측치 및 이상치 처리**: Null값 제거 및 별점 범위 수정 


* **텍스트 데이터 전처리**: 특수문자/불용어 제거 및 비정상적인 길이의 리뷰 필터링 


* **파생 변수 생성**: 시간대, 요일별 리뷰 개수 등 1가지 이상의 변수 생성 


* **텍스트 벡터화**: TF-IDF 또는 Word2Vec 등을 활용한 임베딩 



3) 비교 분석 

사이트 간 키워드 빈도, 감정 분석 결과 및 시계열 추이를 비교 분석한 시각화 자료를 포함합니다.

4) 전처리 실행 방법 

```bash
# review_analysis/preprocessing/ 경로에서 실행
python main.py --output_dir database --all

```

---

## 4-2. GitHub 협업 과제 

1) Branch Protection Rule 설정 

`main` 브랜치에 직접적인 `push`를 금지하고, 반드시 `Pull Request`와 리뷰를 거치도록 설정하였습니다.

* **브랜치 보호 규칙 적용 스크린샷**  
![Branch Protection 적용 화면](github/branch_protection.png)



* **직접 Push 시도 시 거부 화면**  
![Push 거부 로그 화면](github/push_rejected.png)




2) Pull Request & Review 절차 

각 팀원은 개별 브랜치에서 작업 후 PR을 생성하였으며, 팀원의 리뷰 및 승인을 얻어 `merge`를 진행하였습니다.

* **풀리퀘스트 리뷰 및 머지 완료 화면**  
![PR 리뷰 및 머지 화면](github/review_and_merged.png)



---
