from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017")

db = client["bot_stats"]

users = db["users"]
events = db["events"]
