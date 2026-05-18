from pymongo import MongoClient

# CONNECT TO MONGODB
client = MongoClient("mongodb://localhost:27017/")

# CREATE DATABASE
db = client["ai_chat_app"]

# COLLECTIONS
users_collection = db["users"]
messages_collection = db["messages"]
groups_collection = db["groups"]
stories_collection = db["stories"]
contacts_collection = db["contacts"]
