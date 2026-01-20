from __future__ import annotations

import base64
import json
import time
import os
import pandas as pd
import platform
from typing import List, Dict, Any, Optional, cast

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.webdriver import WebDriver as ChromeWebDriver
from selenium.webdriver.remote.webelement import WebElement
from webdriver_manager.chrome import ChromeDriverManager

from review_analysis.crawling.base_crawler import BaseCrawler
from utils.logger import setup_logger

class GoogleMapsCrawler(BaseCrawler):
    """
    Google Map에서 지정된 장소의 상위 리뷰를 수집해서 저장하는 클래스입니다.
    GoogleMapCrawler 단독으로 시행: 
        python -m review_analysis.crawling.google_maps_crawler
    """
    
    def __init__(self, output_dir: str) -> None:
        """
        GoogleMapCrawler class를 초기화합니다.
        output_dir: 크롤링한 정보 (rating, date, content)가 저장될 경로(.csv)를 나타냅니다.
        """

        super().__init__(output_dir)
        self.logger = setup_logger(log_file="google_everland.log")
        self.driver: Optional[ChromeWebDriver] = None
        self.base_url: str = "https://www.google.com/maps"
        self.rows: List[Dict[str, Any]] = []
        self.file_dir = os.path.join(self.output_dir, "reviews_google.csv")
        
        self.logger.info("GoogleMapsCrawler 객체 생성 완료!")
        
    def start_browser(self):
        """
        ChromeDriver(self.driver)를 초기화하고 브라우저를 실행합니다.
        Linux / Windows에 따라 ChromeDriver 경로 설정이 달라집니다.
        """

        try:
            options: Options = Options()
            options.binary_location = "/usr/bin/google-chrome"
            options.add_argument("--lang=ko")
            options.add_argument("--start-maximized")
            options.add_argument("--user-data-dir=/tmp/selenium-profile")
            options.set_capability("goog:loggingPrefs", {"performance": "ALL"})
            options.add_experimental_option("prefs", {
                "intl.accept_languages": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7"
            })
            if platform.system().lower() == "linux":
                options.binary_location = "/usr/bin/google-chrome"
            # options 설정 (Window / Linux 설정 포함)

            self.driver = webdriver.Chrome(
                service=Service(ChromeDriverManager().install()), 
                options=options
            )
            # driver 실행 (새로운 창 열림)

            self.driver.execute_cdp_cmd("Network.enable", {})
            self.driver.execute_cdp_cmd("Network.setCacheDisabled", {"cacheDisabled": True})
            # Network 설정 (안정성 증가)

            self.logger.info("브라우저 실행 완료!")

        except Exception as e:
            self.logger.error(f"브라우저 실행 중 에러 발생: {str(e)}")

    def scrape_reviews(self, review_count: int = 500):
        """
        review_count만큼 리뷰를 수집합니다.
        관련도순(기본)의 상위 리뷰를 기준으로 합니다.
        """

        self.start_browser()
        # brower 시작 (self.driver 할당)

        if self.driver is None:
            raise RuntimeError("driver가 지정되지 않았습니다")
        
        self.driver.get(self.base_url)
        # base_url로 이동

        WebDriverWait(self.driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "input"))
        ).send_keys("에버랜드" + Keys.ENTER)
        WebDriverWait(self.driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "[aria-label=\"에버랜드 리뷰\"]"))
        ).click()
        # 리뷰가 적힌 사이드바로 이동

        while len(self.rows) < review_count:
            scroll_element: WebElement = WebDriverWait(self.driver, 10).until(
                lambda d: d.execute_script("""
                    const root = document.querySelector('div[role="main"]');
                    const el = [...root.querySelectorAll('div')].find(d => d.scrollHeight > d.clientHeight + 50);
                    return el;
                """)
            )
            self.driver.execute_script("arguments[0].scrollTop += 10000;", scroll_element)
            # 맨 밑으로 스크롤하기

            target_file: str = "/maps/rpc/listugcposts"
            target_request_id: Optional[str] = None
            logs = self.driver.get_log("performance")
            for entry in logs:
                msg = json.loads(entry["message"])["message"]
                if msg.get("method") == "Network.responseReceived":
                    url = msg["params"]["response"]["url"]
                    if target_file in url:
                        target_request_id = msg["params"]["requestId"]
            # 리뷰 정보 담긴 request_id 저장

            time.sleep(0.5)
            if target_request_id:
                response_body = self.driver.execute_cdp_cmd('Network.getResponseBody', {'requestId': target_request_id})                                        
                raw_data = response_body['body']
                if response_body.get('base64Encoded'):
                    raw_data = base64.b64decode(raw_data).decode('utf-8')
                clean_json_str: str = raw_data.replace(")]}'", "").strip()
                data: Any = json.loads(clean_json_str)
                # request_id 이용해서 리뷰 정보를 json 포맷으로 받아오기

                for post in data[2]:
                    if len(self.rows) >= review_count:
                        break
                    # 데이터가 review_count 이상이면 중단
                    try:
                        review_rate: float = float(post[0][2][0][0])
                        review_date: str = ".".join(map(str, post[0][2][2][0][1][21][6][8][:3])) + "."
                        review_content: str = post[0][2][15][0][0]
                        # rate, date, content 가져오기

                        if review_content is None:
                            continue 
                        review_content = review_content.replace('\n', ' ').strip()
                        if review_content[0] == "\"" and review_content[-1] == "\"":
                            review_content = review_content[1:-1]
                        # content 형식 맞추기

                        self.rows.append({
                            "rating": review_rate, 
                            "date": review_date,
                            "content": review_content    
                        })
                        # self.rows에 정보 저장

                    except:
                        pass

        self.driver.quit()
        self.logger.info("크롤링 완료!")
        # 드라이버 종료

    def save_to_database(self):
        """
        크롤링한 데이터를 output_dir에 저장합니다.
        데이터가 이미 저장되어 있을 경우 그 뒤에 데이터를 삽입합니다.
        """
        df: pd.DataFrame = pd.DataFrame(self.rows, columns=["rating", "date", "content"])
        df.to_csv(self.file_dir, mode="w", index=False, encoding="utf-8-sig")
        self.logger.info(f"{self.file_dir}로 데이터 저장 완료!")
        # dataFrame으로 변환한 후 output_dir에 csv 형식으로 저장

if __name__ == "__main__":
    crawler: GoogleMapsCrawler = GoogleMapsCrawler(output_dir = "database/reviews_google.csv")
    crawler.scrape_reviews()
    crawler.save_to_database()
    