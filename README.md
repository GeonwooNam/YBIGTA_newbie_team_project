## 에버랜드 리뷰 크롤링 프로젝트
- python -m review_analysis.crawling.main -o database --all 으로 실행
- 크롤링한 사이트: "https://www.google.com/maps", ...
- - main.py의 CRAWLER_CLASSES에 {"크롤러 이름", "크롤러 객체"} 형태로 저장
- 데이터 형식: "별점", "날짜", "리뷰 내용"으로 구성
- 실행 결과는 database/reviews_{파일 이름}.csv로 저장됨
