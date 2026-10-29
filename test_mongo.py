import os
import certifi
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()

client = MongoClient(os.environ["MONGO_URI"], tlsCAFile=certifi.where())
db = client["backup_demo"]

db.test.insert_one({"message": "hello from cloud"})
print("Connected. Document in cloud:", db.test.find_one({}, {"_id": 0}))
