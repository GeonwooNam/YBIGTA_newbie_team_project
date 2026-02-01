from pymongo import MongoClient
from dotenv import load_dotenv
import os

load_dotenv()

mongo_url = os.getenv("MONGO_URL")

mongo_client = MongoClient(mongo_url)

mongo_db = mongo_client.get_database()

