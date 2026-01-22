import time
import os
import pandas as pd
from datetime import datetime
from typing import List, Dict, Any

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

from review_analysis.crawling.base_crawler import BaseCrawler
from utils.logger import setup_logger


class KakaoMapCrawler(BaseCrawler):
    """
    카카오맵 리뷰를 배치 단위로 로드하고 중간 저장 기능을 포함하여 수집하는 크롤러입니다.
    """

    SELECTORS = {
        "review_list": "ul.list_review > li",
        "sort_dropdown": "button.btn_sort",
        "sort_latest": "ul.list_sort li:nth-child(2) a.link_sort",
        "star": "span.starred_grade > span.screen_out:nth-of-type(2)",
        "date": "span.txt_date",
        "content": "p.desc_review",
        "content_more_btn": "span.btn_more"
    }

    def __init__(self, output_dir: str):
        """
        초기화 시점에 출력 경로와 파일명을 확정합니다.
        """
        super().__init__(output_dir)
        self.base_url = 'https://place.map.kakao.com/784414359#review'  # 에버랜드
        self.logger = setup_logger('kakao_everland.log')

        # 중간 저장을 위한 파일명 고정 (시작 시각 기준)
        # now = datetime.now().strftime("%Y%m%d_%H%M%S")
        # self.file_name = f"reviews_kakao_{now}.csv"
        self.file_name = f"reviews_kakao.csv"
        self.file_path = os.path.join(self.output_dir, self.file_name)

        self.driver = None
        self.total_collected = 0  # 실내용 리뷰 카운트
        self.last_processed_idx = 0  # 이미 처리한 DOM 요소 인덱스

        self.logger.info(f"에버랜드 크롤러 준비 완료. 저장 파일: {self.file_name}")

    def start_browser(self):
        """브라우저 실행 및 정렬 전처리를 수행합니다."""
        try:
            options = Options()
            options.add_argument("--start-maximized")
            self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
            self.driver.get(self.base_url)
            time.sleep(3)
            self._change_to_latest_order()
        except Exception as e:
            self.logger.error(f"브라우저 시작 실패: {e}")
            raise

    def _change_to_latest_order(self):
        """리뷰 정렬을 최신순으로 변경합니다."""
        try:
            # 리뷰 정렬 버튼 클릭
            wait = WebDriverWait(self.driver, 10)
            dropdown = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, self.SELECTORS["sort_dropdown"])))
            self.driver.execute_script("arguments[0].click();", dropdown)
            time.sleep(1)

            # 최신순 버튼 클릭
            latest_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, self.SELECTORS["sort_latest"])))
            self.driver.execute_script("arguments[0].click();", latest_btn)
            time.sleep(2)
        except Exception as e:
            self.logger.error(f"정렬 변경 중 오류 (무시하고 진행): {e}")

    def scrape_reviews(self):
        """
        배치 단위 수집 및 중간 저장 로직을 실행합니다.

        이 메서드는 다음과 같은 상세 로직을 수행합니다:
        1. [전처리] 정렬 기준 변경: 분석의 신뢰성을 위해 '최신 순'으로 정렬을 수행합니다.
        2. [루프] 목표 수치 달성 확인: '실내용이 있는 리뷰'가 500개에 도달할 때까지 반복합니다.
        3. [배치 로드] 새로운 요소 추출: DOM에 새로 추가된 'li' 요소들을 인덱스 기반으로 선별합니다.
        4. [데이터 정제 및 확장]:
           - 각 리뷰의 '더보기' 버튼을 클릭하여 숨겨진 텍스트를 노출시킵니다.
           - 별점 전용 리뷰(내용 없음)를 필터링하여 유효한 데이터만 배처화합니다.
        5. [중간 저장] Checkpoint 기능: 배치 처리가 완료될 때마다 CSV 파일에 Append 모드로 즉시 기록하여
           프로그램 강제 종료 시에도 수집된 데이터를 보존합니다.
        6. [종료 처리]: 목표 개수 달성 시 또는 3회 이상 스크롤에도 추가 로딩이 없을 경우 리소스를 해제하고 종료합니다.
        """
        self.start_browser()

        try:
            while self.total_collected < 500:
                # 1. 현재 로드된 모든 리뷰 요소 가져오기
                all_elements = self.driver.find_elements(By.CSS_SELECTOR, self.SELECTORS["review_list"])

                # 2. 새로 로드된 요소만 추출 (last_processed_idx 이후부터)
                new_elements = all_elements[self.last_processed_idx:]

                if not new_elements:
                    # 새로 로드된 게 없으면 스크롤
                    self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    time.sleep(2)
                    # 스크롤 후에도 변화가 없으면 진짜 끝인 지 확인 (에버랜드는 충분할 것임)
                    if len(self.driver.find_elements(By.CSS_SELECTOR,
                                                     self.SELECTORS["review_list"])) == self.last_processed_idx:
                        self.logger.warning("더 이상 새로운 리뷰가 없습니다.")
                        break
                    continue

                batch_data = []
                for el in new_elements:
                    try:
                        # 리뷰 펼치기
                        try:
                            more_btn = el.find_element(By.CSS_SELECTOR, self.SELECTORS["content_more_btn"])
                            if more_btn.text == "더보기":
                                self.driver.execute_script("arguments[0].click();", more_btn)
                        except:
                            pass  # 더보기 버튼 없는 짧은 리뷰

                        content = el.find_element(By.CSS_SELECTOR, self.SELECTORS["content"]).get_attribute(
                            "textContent").strip()

                        # 내용이 있는 리뷰만 처리
                        if content:
                            rating = el.find_element(By.CSS_SELECTOR, self.SELECTORS["star"]).get_attribute(
                                "textContent").strip()
                            date = el.find_element(By.CSS_SELECTOR, self.SELECTORS["date"]).text

                            batch_data.append({
                                "rating": rating,
                                "date": date,
                                "content": content.replace("더보기", "").replace("접기", "").strip()
                            })
                            self.total_collected += 1

                        if self.total_collected >= 500:
                            break
                    except Exception as e:
                        self.logger.debug(f"개별 요소 파싱 실패(무시): {e}")
                        continue

                # 3. 중간 저장 (Append 모드)
                if batch_data:
                    self._intermediate_save(batch_data)
                    self.logger.info(f"중간 저장 완료! 현재 실내용 리뷰: {self.total_collected}개")

                # 인덱스 업데이트
                self.last_processed_idx += len(new_elements)

                # 다음 배치를 위해 스크롤
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(1.5)

        except Exception as e:
            self.logger.error(f"수집 중 치명적 오류 발생: {e}")
        finally:
            self.driver.quit()
            self.logger.info(f"크롤링 종료. 최종 수집: {self.total_collected}개")

    def _intermediate_save(self, data: List[Dict[str, Any]]):
        """데이터를 CSV 파일에 즉시 추가합니다."""
        df = pd.DataFrame(data)
        # 파일이 존재하지 않으면 헤더를 포함하여 생성, 있으면 헤더 없이 이어쓰기
        header = not os.path.exists(self.file_path)
        df.to_csv(self.file_path, mode='a', index=False, header=header, encoding='utf-8-sig')

    def save_to_database(self):
        """이미 중간 저장이 완료되었으므로 최종 확인 로그만 남깁니다."""
        if os.path.exists(self.file_path):
            self.logger.info(f"최종 데이터가 성공적으로 보존되었습니다: {self.file_path}")
        else:
            self.logger.error("최종 데이터 파일을 찾을 수 없습니다.")