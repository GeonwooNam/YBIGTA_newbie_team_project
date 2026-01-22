"""
Trip.com 크롤러 모듈

에버랜드 리뷰를 Trip.com에서 크롤링하는 클래스입니다.
별점, 리뷰 내용, 날짜를 추출하여 CSV 파일로 저장합니다.
"""
from typing import List, Dict, Optional, Set, Union, cast
from dataclasses import dataclass
import time
import csv
import os
import re
from datetime import datetime
from bs4 import BeautifulSoup, Tag
import requests  # type: ignore[import-untyped]
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, StaleElementReferenceException
from webdriver_manager.chrome import ChromeDriverManager
from review_analysis.crawling.base_crawler import BaseCrawler
from utils.logger import setup_logger

@dataclass
class ReviewItem:
    """리뷰 아이템 데이터 클래스"""
    rating: float
    date: str
    text: str
    
    def to_dict(self) -> Dict[str, str]:
        """CSV 저장용 딕셔너리로 변환"""
        return {
            'rating': str(self.rating),
            'date': self.date,
            'text': self.text
        }
    
    def dedup_key(self) -> str:
        """중복 체크용 키 생성"""
        return f"{self.rating}|{self.date}|{self.text[:50]}"

class TripComCrawler(BaseCrawler):
    """
    Trip.com에서 에버랜드 리뷰를 크롤링하는 클래스
    
    Attributes:
        output_dir (str): 출력 파일 디렉토리
        seed_url (str): 크롤링할 Trip.com URL
        driver (Optional[webdriver.Chrome]): Selenium 웹드라이버 인스턴스
        reviews (List[ReviewItem]): 크롤링한 리뷰 데이터 리스트
        logger: 로거 인스턴스
        min_reviews (int): 최소 크롤링할 리뷰 개수
    """
    
    def __init__(self, output_dir: str):
        """
        TripComCrawler 초기화
        
        Args:
            output_dir (str): 출력 파일이 저장될 디렉토리 경로
        """
        super().__init__(output_dir)
        # 기본 URL (review 페이지)
        self.seed_url = 'https://us.trip.com/review/everland-10558712-244874246?locale=en-US&curr=KRW'
        self.driver: Optional[webdriver.Chrome] = None
        self.reviews: List[ReviewItem] = []
        self.logger = setup_logger('tripcom_crawler.log')
        self.min_reviews = 500
        self.seen_keys: Set[str] = set()
        # 크롤링 시작 시 중복 체크 초기화
        self.logger.info("TripComCrawler 초기화 완료")
    
    def start_browser(self) -> None:
        """
        Chrome 브라우저를 시작하고 웹드라이버를 초기화합니다.
        Selenium fallback 용도로만 사용됩니다.
        """
        try:
            chrome_options = Options()
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-blink-features=AutomationControlled')
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36')
            
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            self.driver.implicitly_wait(10)
            self.logger.info("브라우저 시작 완료 (Selenium fallback)")
        except Exception as e:
            self.logger.error(f"브라우저 시작 실패: {str(e)}")
            raise
    
    def _fetch_html_requests(self, url: str, max_retries: int = 3) -> Optional[str]:
        """
        requests를 사용하여 HTML을 가져옵니다.
        
        Args:
            url (str): 요청할 URL
            max_retries (int): 최대 재시도 횟수
            
        Returns:
            Optional[str]: HTML 문자열, 실패 시 None
        """
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
        }
        
        for attempt in range(max_retries):
            try:
                response = requests.get(url, headers=headers, timeout=10)
                response.raise_for_status()
                time.sleep(0.3)  # 요청 간 지연
                return response.text
            except requests.RequestException as e:
                self.logger.warning(f"요청 실패 (시도 {attempt + 1}/{max_retries}): {str(e)}")
                if attempt < max_retries - 1:
                    time.sleep(1)
                else:
                    return None
        return None
    
    def _fetch_html_selenium(self, url: str) -> Optional[str]:
        """
        Selenium을 사용하여 HTML을 가져옵니다 (fallback).
        
        Args:
            url (str): 요청할 URL
            
        Returns:
            Optional[str]: HTML 문자열, 실패 시 None
        """
        if not self.driver:
            self.start_browser()
        
        if not self.driver:
            return None
        
        try:
            self.driver.get(url)
            time.sleep(3)
            return self.driver.page_source
        except Exception as e:
            self.logger.error(f"Selenium으로 HTML 가져오기 실패: {str(e)}")
            return None
    
    def _normalize_date(self, raw_date: str) -> str:
        """
        날짜 문자열을 정규화합니다 (ISO 형태로 변환 시도).
        
        Args:
            raw_date (str): 원본 날짜 문자열
            
        Returns:
            str: 정규화된 날짜 문자열 (실패 시 원문 반환)
        """
        if not raw_date:
            return ""
        
        # "Reviewed on Jan 11, 2026" 형태 파싱
        patterns = [
            (r'Reviewed on (\w+) (\d+), (\d{4})', '%B %d, %Y'),
            (r'(\d{4})-(\d{2})-(\d{2})', '%Y-%m-%d'),
            (r'(\d{2})/(\d{2})/(\d{4})', '%m/%d/%Y'),
            (r'(\d{4})년 (\d{1,2})월 (\d{1,2})일', '%Y-%m-%d'),
        ]
        
        # 월 이름 매핑
        month_map = {
            'Jan': 'January', 'Feb': 'February', 'Mar': 'March',
            'Apr': 'April', 'May': 'May', 'Jun': 'June',
            'Jul': 'July', 'Aug': 'August', 'Sep': 'September',
            'Oct': 'October', 'Nov': 'November', 'Dec': 'December'
        }
        
        for pattern, date_format in patterns:
            match = re.search(pattern, raw_date)
            if match:
                try:
                    if len(match.groups()) == 3:
                        if pattern.startswith('Reviewed on'):
                            month_name = match.group(1)
                            month_name = month_map.get(month_name, month_name)
                            date_str = f"{month_name} {match.group(2)}, {match.group(3)}"
                        else:
                            date_str = raw_date[match.start():match.end()]
                        
                        dt = datetime.strptime(date_str, date_format)
                        return dt.strftime('%Y-%m-%d')
                except (ValueError, IndexError):
                    continue
        
        # 정규화 실패 시 원문 반환 (strip 처리)
        return raw_date.strip()
    
    def _parse_rating(self, element: Union[BeautifulSoup, Tag]) -> Optional[float]:
        """
        리뷰 요소에서 별점을 추출합니다.
        새로운 구조: <span class="review_score">5</span>
        
        Args:
            element (Union[BeautifulSoup, Tag]): 리뷰 요소
            
        Returns:
            Optional[float]: 별점 (1-5), 추출 실패 시 None
        """
        try:
            # 새로운 구조: <span class="review_score">5</span>
            rating_span = element.find('span', class_='review_score')
            if rating_span:
                # score-name 클래스는 제외 (Outstanding 같은 텍스트)
                classes = rating_span.get('class')
                if classes and isinstance(classes, (list, tuple)) and 'score-name' not in list(classes):
                    rating_text = rating_span.get_text(strip=True)
                    match = re.search(r'(\d+\.?\d*)', rating_text)
                    if match:
                        rating = float(match.group(1))
                        if 1.0 <= rating <= 5.0:
                            return rating
        except (ValueError, AttributeError, TypeError) as e:
            self.logger.debug(f"별점 추출 오류: {str(e)}")
        
        return None
    
    def _parse_date(self, element: Union[BeautifulSoup, Tag]) -> Optional[str]:
        """
        리뷰 요소에서 날짜를 추출합니다.
        새로운 구조: <span>Posted: Jan 10, 2026</span>
        
        Args:
            element (BeautifulSoup): 리뷰 요소
            
        Returns:
            Optional[str]: 날짜 문자열, 추출 실패 시 None
        """
        try:
            # "Posted: " 텍스트를 포함한 span 요소 찾기
            # 모든 span을 확인
            spans = element.find_all('span')
            for span in spans:
                text = span.get_text(strip=True)
                if text and text.startswith('Posted:'):
                    # "Posted: " 제거하고 날짜 부분만 추출
                    date_str = text.replace('Posted:', '').strip()
                    if date_str:
                        normalized = self._normalize_date(date_str)
                        if normalized:
                            return normalized
            
            # "Posted:" 없이 날짜만 있는 경우도 시도
            for span in spans:
                text = span.get_text(strip=True)
                if text and re.search(r'Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec', text):
                    normalized = self._normalize_date(text)
                    if normalized:
                        return normalized
        except (AttributeError, TypeError, ValueError) as e:
            self.logger.debug(f"날짜 추출 오류: {str(e)}")
        
        return None
    
    def _parse_text(self, element: Union[BeautifulSoup, Tag]) -> Optional[str]:
        """
        리뷰 요소에서 리뷰 텍스트를 추출합니다.
        새로운 구조: <div class="burited_point"><p class="show-lines-review-text-5">...</p></div>
        
        Args:
            element (BeautifulSoup): 리뷰 요소
            
        Returns:
            Optional[str]: 리뷰 텍스트, 추출 실패 시 None
        """
        try:
            # 방법 1: burited_point div 내부의 p 태그
            burited_div = element.find('div', class_='burited_point')
            if burited_div:
                p_tag = burited_div.find('p', class_=re.compile(r'show-lines-review-text'))
                if p_tag:
                    text = p_tag.get_text(separator=' ', strip=True)
                    if text and len(text) > 5:
                        return text
                # p 태그를 못 찾으면 div 내부 텍스트 직접 추출
                text = burited_div.get_text(separator=' ', strip=True)
                if text and len(text) > 5:
                    return text
            
            # 방법 2: show-lines-review-text 클래스를 가진 p 태그 직접 찾기
            p_tag = element.find('p', class_=re.compile(r'show-lines-review-text'))
            if p_tag:
                text = p_tag.get_text(separator=' ', strip=True)
                if text and len(text) > 5:
                    return text
            
        except (AttributeError, TypeError, ValueError) as e:
            self.logger.debug(f"리뷰 텍스트 추출 오류: {str(e)}")
        
        return None
    
    def _parse_reviews(self, html: str) -> List[ReviewItem]:
        """
        HTML에서 리뷰를 파싱합니다.
        새로운 구조에 맞춰 파싱: review_score, burited_point, Posted 날짜
        
        Args:
            html (str): HTML 문자열
            
        Returns:
            List[ReviewItem]: 파싱된 리뷰 리스트
        """
        reviews: List[ReviewItem] = []
        soup = BeautifulSoup(html, 'html.parser')
        
        # 새로운 구조: review_score를 가진 요소를 기준으로 리뷰 카드 찾기
        # 방법 1: review_score 기준으로 찾기
        review_scores = soup.find_all('span', class_='review_score')
        
        # 각 별점의 가장 가까운 공통 부모 요소(리뷰 카드) 찾기
        review_items = []
        processed_parents = set()
        
        for score_span in review_scores:
            # score-name은 제외 (Outstanding 같은 텍스트)
            classes = score_span.get('class')
            if classes and isinstance(classes, list) and 'score-name' in classes:
                continue
            
            # 부모 요소들을 거슬러 올라가며 리뷰 카드 찾기
            parent = score_span.find_parent()
            review_card = None
            
            # 몇 단계 위로 올라가며 적절한 리뷰 카드 찾기
            for _ in range(15):  # 더 많이 올라가도록 범위 증가
                if not parent:
                    break
                    
                # 이 부모가 review_score와 burited_point 둘 다 포함하는지 확인
                has_rating = parent.find('span', class_='review_score') is not None
                has_text = parent.find('div', class_='burited_point') is not None or parent.find('p', class_=re.compile(r'show-lines-review-text')) is not None
                has_date = any('Posted:' in span.get_text() for span in parent.find_all('span') if span.get_text())
                
                if has_rating and (has_text or has_date):
                    parent_id = id(parent)
                    if parent_id not in processed_parents:
                        review_card = parent
                        processed_parents.add(parent_id)
                        break
                
                parent = parent.find_parent()
            
            if review_card:
                review_items.append(review_card)
        
        # 방법 2: burited_point 기준으로도 찾기 (보완)
        if len(review_items) < 5:  # 리뷰가 적게 찾아졌을 때
            burited_divs = soup.find_all('div', class_='burited_point')
            for burited_div in burited_divs:
                parent = burited_div.find_parent()
                if parent is None:
                    continue
                parent_id = id(parent)
                
                # 이미 처리한 부모가 아니고, rating이 있는 경우
                if parent_id not in processed_parents:
                    if parent.find('span', class_='review_score'):
                        review_items.append(cast(Tag, parent))
                        processed_parents.add(parent_id)
        
        self.logger.info(f"찾은 리뷰 항목 수: {len(review_items)}")
        
        if not review_items:
            self.logger.warning("리뷰 항목을 찾을 수 없음 - HTML 구조 확인 필요")
            return reviews
        
        for item in review_items:
            try:
                rating = self._parse_rating(item)
                date = self._parse_date(item)
                text = self._parse_text(item)
                
                # 필수 필드 검증
                if rating is not None and date and text and len(text) > 5:
                    review = ReviewItem(rating=rating, date=date, text=text)
                    
                    # 중복 체크
                    key = review.dedup_key()
                    if key not in self.seen_keys:
                        self.seen_keys.add(key)
                        reviews.append(review)
                    else:
                        self.logger.debug(f"중복 리뷰 제외: {text[:30]}...")
                else:
                    self.logger.debug(f"리뷰 데이터 불완전 - rating: {rating}, date: {bool(date)}, text: {bool(text) and len(text) if text else 0}")
            except Exception as e:
                self.logger.debug(f"리뷰 파싱 오류: {str(e)}")
                continue
        
        return reviews
    
    def _get_page_url(self, page: int) -> str:
        """
        페이지 번호에 따른 URL을 생성합니다.
        
        Args:
            page (int): 페이지 번호 (1부터 시작)
            
        Returns:
            str: 페이지 URL
        """
        # Trip.com은 메인 페이지에서 리뷰를 보여주므로 URL 변경 없이 버튼 클릭 방식 사용
        return self.seed_url
    
    def _click_next_button(self) -> bool:
        """
        다음 페이지 버튼을 클릭합니다.
        새로운 구조: 페이지 번호를 클릭하거나 btn-quicknext 버튼 클릭
        
        Returns:
            bool: 클릭 성공 여부
        """
        if not self.driver:
            return False
        
        try:
            # **중요**: 버튼 클릭 전에 현재 페이지의 리뷰 텍스트를 먼저 수집
            current_review_texts = []
            try:
                # 새로운 구조: burited_point 또는 show-lines-review-text를 가진 요소 찾기
                review_elements = self.driver.find_elements(By.CSS_SELECTOR, 'div.burited_point p, p[class*="show-lines-review-text"]')
                for elem in review_elements[:3]:
                    try:
                        text = elem.text.strip()
                        if text and len(text) > 10:
                            current_review_texts.append(text[:100])
                    except:
                        continue
                self.logger.info(f"📌 클릭 전 현재 페이지 리뷰 샘플: {len(current_review_texts)}개")
                if current_review_texts:
                    self.logger.debug(f"   첫 번째 리뷰 (참조용): {current_review_texts[0][:50]}...")
            except Exception as e:
                self.logger.warning(f"현재 리뷰 찾기 실패: {str(e)}")
            
            # 현재 활성화된 페이지 번호 찾기
            try:
                active_page = self.driver.find_element(By.CSS_SELECTOR, 'li.number.active')
                current_page_num = int(active_page.text.strip())
                next_page_num = current_page_num + 1
                self.logger.info(f"현재 페이지: {current_page_num}, 다음 페이지: {next_page_num}")
            except Exception as e:
                self.logger.debug(f"페이지 번호 찾기 실패: {str(e)}, 기본값(2) 사용")
                next_page_num = 2  # 기본값
            
            click_success = False
            clicked_button_type = None
            
            # 방법 1: 다음 페이지 번호 클릭 시도 (review 페이지 - 숫자로 된 페이지네이션)
            if not click_success:
                next_page_elem = None
                try:
                    # 여러 방법으로 다음 페이지 번호 찾기
                    xpath_attempts = [
                        f"//li[@class='number' and normalize-space(text())='{next_page_num}']",  # 공백 제거
                        f"//li[contains(@class, 'number') and normalize-space(text())='{next_page_num}']",  # class에 number 포함
                        f"//li[@class='number' and text()='{next_page_num}']",  # 원본
                    ]
                    
                    for xpath in xpath_attempts:
                        try:
                            next_page_elem = self.driver.find_element(By.XPATH, xpath)
                            self.logger.debug(f"페이지 {next_page_num} 번호 찾음 (XPATH: {xpath[:50]}...)")
                            break
                        except NoSuchElementException:
                            continue
                except Exception as e:
                    self.logger.debug(f"페이지 번호 찾기 중 예외: {str(e)}")
                
                if next_page_elem:
                    # 버튼 상태 확인
                    is_visible = next_page_elem.is_displayed()
                    is_enabled = next_page_elem.is_enabled()
                    class_attr = next_page_elem.get_attribute('class') or ""
                    
                    self.logger.info(f"🔍 페이지 {next_page_num} 번호 발견 (visible: {is_visible}, enabled: {is_enabled}, class: {class_attr})")
                    
                    # disabled나 active 클래스가 있으면 클릭하지 않음
                    if 'disabled' in class_attr.lower() or 'active' in class_attr.lower():
                        self.logger.warning(f"페이지 {next_page_num} 번호가 클릭 불가 상태 (class: {class_attr})")
                        click_success = False
                    elif is_visible:
                        self.driver.execute_script("arguments[0].scrollIntoView({block: 'center', behavior: 'smooth'});", next_page_elem)
                        time.sleep(0.8)  # 스크롤 후 안정화 대기 증가
                        
                        # 여러 방법으로 클릭 시도
                        click_attempts_success = False
                        
                        # 방법 1-1: JavaScript 클릭 (가장 확실)
                        try:
                            self.driver.execute_script("arguments[0].click();", next_page_elem)
                            self.logger.info(f"✅ 페이지 {next_page_num} 번호 JavaScript 클릭 완료")
                            click_attempts_success = True
                        except Exception as e_js:
                            self.logger.debug(f"JavaScript 클릭 실패: {str(e_js)}")
                        
                        # 방법 1-2: ActionChains 클릭 (보조)
                        if not click_attempts_success:
                            try:
                                ActionChains(self.driver).move_to_element(next_page_elem).click().perform()
                                self.logger.info(f"✅ 페이지 {next_page_num} 번호 ActionChains 클릭 완료")
                                click_attempts_success = True
                            except Exception as e_action:
                                self.logger.debug(f"ActionChains 클릭 실패: {str(e_action)}")
                        
                        # 방법 1-3: 직접 클릭 (최후 수단)
                        if not click_attempts_success:
                            try:
                                next_page_elem.click()
                                self.logger.info(f"✅ 페이지 {next_page_num} 번호 직접 클릭 완료")
                                click_attempts_success = True
                            except Exception as e_direct:
                                self.logger.debug(f"직접 클릭 실패: {str(e_direct)}")
                        
                        if click_attempts_success:
                            click_success = True
                            clicked_button_type = f"페이지 번호 {next_page_num}"
                        else:
                            self.logger.error(f"❌ 페이지 {next_page_num} 번호 모든 클릭 방법 실패")
                    else:
                        self.logger.debug(f"페이지 {next_page_num} 번호가 화면에 보이지 않음")
                else:
                    self.logger.debug(f"페이지 {next_page_num} 번호를 찾을 수 없음 (모든 XPATH 시도 실패)")
            
            # 방법 2: btn-quicknext 또는 더보기 버튼 클릭
            if not click_success:
                try:
                    quick_next = self.driver.find_element(By.CSS_SELECTOR, 'li.btn-quicknext, li.gl-cpt-icon-more')
                    if quick_next and quick_next.is_displayed():
                        self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", quick_next)
                        time.sleep(0.3)
                        ActionChains(self.driver).move_to_element(quick_next).click().perform()
                        self.logger.info("✅ 더보기/다음 버튼(btn-quicknext) 클릭 성공")
                        click_success = True
                        clicked_button_type = "btn-quicknext"
                    else:
                        self.logger.debug("btn-quicknext 버튼이 화면에 보이지 않음")
                except NoSuchElementException:
                    self.logger.debug("btn-quicknext 버튼을 찾을 수 없음")
                except Exception as e:
                    self.logger.debug(f"btn-quicknext 클릭 시도 실패: {str(e)}")
            
            # 방법 3: btn-next 버튼 클릭 (fallback)
            if not click_success:
                try:
                    next_button = self.driver.find_element(By.CSS_SELECTOR, 'button.btn-next')
                    disabled = next_button.get_attribute('disabled')
                    class_attr = next_button.get_attribute('class') or ""
                    is_displayed = next_button.is_displayed()
                    
                    self.logger.info(f"🔍 btn-next 버튼 발견 (visible: {is_displayed}, enabled: {not disabled}, class: {class_attr})")
                    
                    if not disabled and 'disabled' not in class_attr.lower() and is_displayed:
                        self.driver.execute_script("arguments[0].scrollIntoView({block: 'center', behavior: 'smooth'});", next_button)
                        time.sleep(0.8)
                        
                        # JavaScript 클릭 시도
                        try:
                            self.driver.execute_script("arguments[0].click();", next_button)
                            self.logger.info("✅ btn-next 버튼 JavaScript 클릭 완료")
                            click_success = True
                            clicked_button_type = "button.btn-next"
                        except Exception as e_js:
                            self.logger.debug(f"JavaScript 클릭 실패, ActionChains 시도: {str(e_js)}")
                            try:
                                ActionChains(self.driver).move_to_element(next_button).click().perform()
                                self.logger.info("✅ btn-next 버튼 ActionChains 클릭 완료")
                                click_success = True
                                clicked_button_type = "button.btn-next"
                            except Exception as e_action:
                                self.logger.debug(f"ActionChains 클릭 실패: {str(e_action)}")
                    else:
                        self.logger.debug(f"btn-next 버튼 클릭 불가 (disabled: {disabled}, class: {class_attr})")
                except NoSuchElementException:
                    self.logger.debug("button.btn-next 버튼을 찾을 수 없음")
                except Exception as e:
                    self.logger.debug(f"btn-next 클릭 시도 실패: {str(e)}")
            
            if not click_success:
                # 모든 버튼 시도 실패 시, 페이지네이션 구조 확인
                self.logger.warning("❌ 모든 페이지네이션 버튼을 찾을 수 없거나 클릭할 수 없음")
                try:
                    # 디버깅: 페이지네이션 구조 확인
                    all_pagination = self.driver.find_elements(By.CSS_SELECTOR, 'li.number, li.btn-quicknext, button.btn-next')
                    self.logger.debug(f"페이지네이션 요소 개수: {len(all_pagination)}")
                    for i, elem in enumerate(all_pagination[:10]):  # 처음 10개만
                        try:
                            tag = elem.tag_name
                            text = elem.text.strip()[:20]
                            class_attr = elem.get_attribute('class') or ""
                            self.logger.debug(f"  요소 {i+1}: <{tag}> class='{class_attr}' text='{text}'")
                        except:
                            pass
                except Exception as e:
                    self.logger.debug(f"페이지네이션 구조 확인 실패: {str(e)}")
                return False
            
            # 클릭 후 짧은 대기 (페이지 로딩 시간)
            self.logger.info(f"⏳ {clicked_button_type} 클릭 후 페이지 로딩 대기 중...")
            time.sleep(3)  # 초기 로딩 대기 시간 더 증가 (JavaScript 로딩 대기)
            
            # 페이지 전환 확인 - 여러 방법으로 검증
            if current_review_texts:
                try:
                    # 최대 20초 대기, 0.5초마다 체크
                    wait_time: float = 0.0
                    max_wait = 20
                    page_changed = False
                    check_count = 0
                    
                    # 방법 1: 활성 페이지 번호가 변경되었는지 확인
                    target_page_num = next_page_num
                    
                    while wait_time < max_wait:
                        time.sleep(0.5)
                        wait_time = wait_time + 0.5
                        check_count += 1
                        
                        try:
                            # 새로운 구조: review_score를 가진 리뷰 항목 찾기
                            new_review_texts = []
                            try:
                                # burited_point 또는 show-lines-review-text를 가진 요소 찾기
                                review_elements = self.driver.find_elements(By.CSS_SELECTOR, 'div.burited_point p, p[class*="show-lines-review-text"]')
                                for elem in review_elements[:3]:
                                    try:
                                        text = elem.text.strip()
                                        if text and len(text) > 10:
                                            new_review_texts.append(text[:100])
                                    except:
                                        continue
                            except:
                                pass
                            
                            # 방법 1-1: 활성 페이지 번호 확인 (가장 확실)
                            try:
                                new_active_page = self.driver.find_element(By.CSS_SELECTOR, 'li.number.active')
                                new_active_page_num = int(new_active_page.text.strip())
                                if new_active_page_num == target_page_num:
                                    self.logger.info(f"✅ 페이지 전환 확인 완료! (활성 페이지: {new_active_page_num}, 대기 시간: {wait_time:.1f}초)")
                                    page_changed = True
                                    break
                                elif check_count % 4 == 0:
                                    self.logger.debug(f"📊 활성 페이지 확인 중... (현재: {new_active_page_num}, 목표: {target_page_num}, 대기: {wait_time:.1f}초)")
                            except (NoSuchElementException, ValueError):
                                pass  # 아직 로딩 중
                            
                            # 방법 1-2: 리뷰 텍스트 비교 (보조 확인)
                            
                            # 리뷰 텍스트가 변경되었는지 확인
                            if new_review_texts and len(new_review_texts) >= 1:
                                if current_review_texts and len(current_review_texts) >= 1:
                                    if new_review_texts[0] != current_review_texts[0]:
                                        self.logger.info(f"✅ 페이지 전환 확인 완료! (리뷰 내용 변경, 대기 시간: {wait_time:.1f}초)")
                                        self.logger.debug(f"   이전 첫 리뷰: {current_review_texts[0][:50]}...")
                                        self.logger.debug(f"   새 첫 리뷰: {new_review_texts[0][:50]}...")
                                        page_changed = True
                                        break
                            
                            # 로그를 2초마다 한 번씩만 출력
                            if check_count % 4 == 0:
                                self.logger.debug(f"📊 페이지 전환 확인 중... (대기: {wait_time:.1f}초, 새 리뷰: {len(new_review_texts)}개)")
                            
                        except (NoSuchElementException, TimeoutException, StaleElementReferenceException):
                            # 아직 로딩 중일 수 있음, 계속 대기
                            if check_count % 4 == 0:
                                self.logger.debug(f"⏳ 아직 로딩 중... (대기: {wait_time:.1f}초)")
                            continue
                        except Exception as e:
                            self.logger.debug(f"페이지 전환 확인 중 예외: {str(e)}")
                            continue
                    
                    if not page_changed:
                        self.logger.error(f"❌ 페이지 전환 확인 실패! ({max_wait}초 대기 후에도 변경 없음)")
                        # 마지막 확인: 현재 활성 페이지 번호
                        try:
                            final_active = self.driver.find_element(By.CSS_SELECTOR, 'li.number.active')
                            final_page_num = int(final_active.text.strip())
                            self.logger.error(f"   현재 활성 페이지: {final_page_num}, 목표 페이지: {target_page_num}")
                        except:
                            pass
                        if current_review_texts:
                            self.logger.error(f"   이전 첫 리뷰 (참조): {current_review_texts[0][:50]}...")
                        # 마지막 시도로 현재 리뷰 확인
                        try:
                            final_review_elements = self.driver.find_elements(By.CSS_SELECTOR, 'div.burited_point p, p[class*="show-lines-review-text"]')
                            if final_review_elements:
                                final_text = final_review_elements[0].text.strip()[:50] if final_review_elements[0].text else "없음"
                                self.logger.error(f"   현재 첫 리뷰: {final_text}...")
                        except:
                            pass
                        return False  # 페이지 전환 실패 시 False 반환
                except Exception as e:
                    self.logger.warning(f"페이지 전환 확인 중 오류: {str(e)}")
                    time.sleep(5)  # 대체 대기
                    return False
            else:
                self.logger.warning("⚠️ 현재 리뷰 텍스트를 찾지 못해 페이지 번호 변경으로만 확인")
                # 리뷰 텍스트 없이도 페이지 번호 변경으로 확인
                time.sleep(2)
                try:
                    final_active = self.driver.find_element(By.CSS_SELECTOR, 'li.number.active')
                    final_page_num = int(final_active.text.strip())
                    if final_page_num == next_page_num:
                        self.logger.info(f"✅ 페이지 전환 확인 완료! (활성 페이지: {final_page_num})")
                        return True
                    else:
                        self.logger.warning(f"⚠️ 페이지 번호 불일치 (현재: {final_page_num}, 목표: {next_page_num}), 3초 더 대기")
                        time.sleep(3)
                        return True  # 일단 진행
                except:
                    self.logger.warning("⚠️ 활성 페이지 확인 실패, 5초 대기 후 진행")
                    time.sleep(5)
                    return True  # 일단 진행
            
            return True
        except (NoSuchElementException, Exception) as e:
            self.logger.debug(f"다음 버튼 클릭 실패: {str(e)}")
            return False
        
        return False
    
    def _is_page_changed(self, driver: webdriver.Chrome, old_text: str) -> bool:
        """페이지가 변경되었는지 확인"""
        try:
            first_item = driver.find_element(By.CSS_SELECTOR, 'li:first-child div.gl-poi-detail_comment-content')
            first_review_p = first_item.find_element(By.CSS_SELECTOR, 'div:nth-child(2) > a > p')
            new_text = first_review_p.text if first_review_p else ""
            return new_text != old_text and len(new_text) > 0
        except:
            return False
    
    def _load_existing_reviews(self) -> None:
        """
        기존 CSV 파일에서 리뷰를 로드하여 중복 체크에 사용합니다.
        """
        csv_file = os.path.join(self.output_dir, 'reviews_tripcom.csv')
        if not os.path.exists(csv_file):
            self.logger.info("기존 CSV 파일이 없습니다. 처음부터 크롤링합니다.")
            return
        
        try:
            with open(csv_file, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                existing_count = 0
                for row in reader:
                    try:
                        rating = float(row['rating'])
                        date = row['date']
                        text = row['text']
                        
                        review = ReviewItem(rating=rating, date=date, text=text)
                        key = review.dedup_key()
                        self.seen_keys.add(key)
                        self.reviews.append(review)
                        existing_count += 1
                    except (ValueError, KeyError) as e:
                        self.logger.debug(f"기존 리뷰 로드 중 오류: {str(e)}")
                        continue
                
                self.logger.info(f"기존 CSV에서 {existing_count}개 리뷰를 로드했습니다. (중복 체크용)")
        except Exception as e:
            self.logger.warning(f"기존 CSV 파일 로드 실패: {str(e)}. 처음부터 크롤링합니다.")
    
    def scrape_reviews(self) -> None:
        """
        리뷰를 크롤링합니다. 최소 개수만큼 크롤링될 때까지 페이지를 순회합니다.
        Selenium을 사용하여 동적 로딩된 리뷰를 크롤링합니다.
        처음부터 크롤링합니다 (기존 CSV 파일은 무시).
        """
        # 처음부터 크롤링 (기존 CSV 파일 로드하지 않음)
        # self._load_existing_reviews()  # 주석 처리: 처음부터 크롤링
        
        initial_count = len(self.reviews)
        
        self.logger.info(f"크롤링 시작: {self.seed_url}")
        self.logger.info(f"처음부터 크롤링합니다 (기존 리뷰: {initial_count}개)")
        self.logger.info(f"목표 리뷰 수: {self.min_reviews}개")
        
        # Selenium 사용 (동적 로딩 필요)
        if not self.driver:
            self.start_browser()
        
        if not self.driver:
            self.logger.error("브라우저를 시작할 수 없습니다.")
            return
        
        try:
            self.driver.get(self.seed_url)
            time.sleep(5)  # 초기 페이지 로딩 대기
            
            # 리뷰 섹션으로 스크롤 (새로운 구조)
            try:
                review_element = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, 'span.review_score, div.burited_point'))
                )
                self.driver.execute_script("arguments[0].scrollIntoView(true);", review_element)
                time.sleep(3)
                self.logger.info("리뷰 섹션으로 스크롤 완료")
            except TimeoutException:
                self.logger.warning("리뷰 요소를 찾을 수 없음, 계속 진행")
            
            # 추가 스크롤로 동적 로딩 트리거
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            
            page = 1
            max_pages = 200
            consecutive_empty_pages = 0
            max_consecutive_empty = 3
            
            while len(self.reviews) < self.min_reviews and page <= max_pages:
                self.logger.info(f"페이지 {page} 크롤링 중 (현재 누적: {len(self.reviews)}개)")
                
                # 현재 페이지 리뷰 파싱
                html = self.driver.page_source
                page_reviews = self._parse_reviews(html)
                
                # 디버깅: HTML 일부 저장 (리뷰를 찾지 못한 경우)
                if not page_reviews and page == 1:
                    # HTML 일부를 로그로 남김
                    if 'review_score' in html:
                        self.logger.debug("review_score 발견됨")
                    if 'burited_point' in html:
                        self.logger.debug("burited_point 발견됨")
                    if 'show-lines-review-text' in html:
                        self.logger.debug("show-lines-review-text 발견됨")
                    else:
                        self.logger.warning("새로운 리뷰 구조 요소가 HTML에 없음")
                
                if not page_reviews:
                    consecutive_empty_pages += 1
                    self.logger.warning(f"페이지 {page}에서 리뷰를 찾을 수 없음 (연속 빈 페이지: {consecutive_empty_pages})")
                    if consecutive_empty_pages >= max_consecutive_empty:
                        self.logger.error("연속 빈 페이지로 크롤링 중단")
                        break
                else:
                    consecutive_empty_pages = 0
                    self.reviews.extend(page_reviews)
                    self.logger.info(f"페이지 {page}에서 {len(page_reviews)}개 리뷰 수집 (총 {len(self.reviews)}개)")
                
                # 목표 달성 체크
                if len(self.reviews) >= self.min_reviews:
                    self.logger.info(f"목표 개수({self.min_reviews}개) 달성: {len(self.reviews)}개 리뷰 크롤링 완료")
                    break
                
                # 다음 페이지로 이동
                if not self._click_next_button():
                    self.logger.info("다음 버튼을 찾을 수 없거나 더 이상 페이지가 없습니다.")
                    break
                
                # 리뷰 섹션으로 다시 스크롤 (새로운 구조에 맞게)
                if self.driver:
                    try:
                        # review_score가 있는 요소로 스크롤
                        review_element = self.driver.find_element(By.CSS_SELECTOR, 'span.review_score')
                        self.driver.execute_script("arguments[0].scrollIntoView(true);", review_element)
                        time.sleep(2)
                    except NoSuchElementException:
                        pass
                    
                    # 추가 대기: 리뷰 항목의 텍스트가 로드될 때까지 (새로운 구조)
                    try:
                        WebDriverWait(self.driver, 10).until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, 'div.burited_point p, p[class*="show-lines-review-text"]'))
                        )
                    except TimeoutException:
                        self.logger.warning("리뷰 텍스트 로드 대기 타임아웃")
                
                page += 1
                time.sleep(1)  # 페이지 간 지연
            
            self.logger.info(f"크롤링 완료: 총 {len(self.reviews)}개 리뷰")
            
        except Exception as e:
            self.logger.error(f"크롤링 중 오류 발생: {str(e)}")
            raise
        finally:
            if self.driver:
                self.driver.quit()
                self.logger.info("브라우저 종료")
    
    def save_to_database(self) -> None:
        """
        크롤링한 리뷰 데이터를 CSV 파일로 저장합니다.
        파일명은 reviews_tripcom.csv입니다.
        기존 파일이 있으면 병합하여 저장합니다.
        """
        try:
            # 출력 디렉토리 생성
            os.makedirs(self.output_dir, exist_ok=True)
            
            # CSV 파일 경로
            output_file = os.path.join(self.output_dir, 'reviews_tripcom.csv')
            
            # CSV 파일에 저장 (기존 + 새로운 리뷰 모두)
            with open(output_file, 'w', newline='', encoding='utf-8-sig') as f:
                if self.reviews:
                    fieldnames = ['rating', 'date', 'text']
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writeheader()
                    for review in self.reviews:
                        writer.writerow(review.to_dict())
                else:
                    # 빈 파일이라도 헤더는 생성
                    writer = csv.DictWriter(f, fieldnames=['rating', 'date', 'text'])
                    writer.writeheader()
            
            self.logger.info(f"CSV 파일 저장 완료: {output_file} ({len(self.reviews)}개 리뷰)")
            
        except Exception as e:
            self.logger.error(f"CSV 저장 중 오류 발생: {str(e)}")
            raise
