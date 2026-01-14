from abc import ABC, abstractmethod
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium import webdriver

######## 수정 금지 #########
class BaseCrawler(ABC):
    def __init__(self, output_dir: str):
        self.output_dir = output_dir

    @abstractmethod
    def start_browser(self):
        pass

    @abstractmethod
    def scrape_reviews(self):
        pass

    @abstractmethod
    def save_to_database(self):
        pass
############################