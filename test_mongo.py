from pymongo import MongoClient
import os

MONGO_URI = os.environ.get("MONGO_URI", "mongodb+srv://ajaykumardeveloper12_db_user:Momdad%40223@ajay.cfzt5ua.mongodb.net/?appName=ajay")
try:
    client = MongoClient(MONGO_URI)
    db = client["jaya_giftshop"]
    print("Connected to MongoDB")
    print("Databases:", client.list_database_names())
    print("Collections in jaya_giftshop:", db.list_collection_names())
except Exception as e:
    print("Error:", e)