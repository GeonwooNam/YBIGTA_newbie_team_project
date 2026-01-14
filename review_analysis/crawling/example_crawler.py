from review_analysis.crawling.base_crawler import BaseCrawler

class ExampleCrawler(BaseCrawler):
    def __init__(self, output_dir: str):
        super().__init__(output_dir)
        self.base_url = 'https://example.com'
        
    def start_browser(self):
        pass 
    
    def scrape_reviews(self):
        pass
    
    def save_to_database(self):
        pass
