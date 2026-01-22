from review_analysis.preprocessing.base_processor import BaseDataProcessor

class ExampleProcessor(BaseDataProcessor):
    def __init__(self, input_path: str, output_path: str):
        super().__init__(input_path, output_path)

    def preprocess(self):
        pass
    
    def feature_engineering(self):
        pass

    def save_to_database(self):
        pass
