from pymongo import MongoClient
from dotenv import load_dotenv
import os
from typing import Any

load_dotenv()

mongo_url = os.getenv("MONGO_URL")

mongo_client: MongoClient[Any] = MongoClient(mongo_url)

# mongo_db = mongo_client.get_database()

db_name = os.getenv("DB_NAME")
mongo_db = mongo_client.get_database(db_name)

