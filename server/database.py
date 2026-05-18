import os
from pymongo import MongoClient

# CONNECT TO MONGODB
# Check for environment variable first (used in Vercel), fallback to localhost
mongo_uri = os.environ.get("MONGODB_URI", "mongodb://localhost:27017/")
client = MongoClient(mongo_uri)

# CREATE DATABASE
db = client["ai_chat_app"]

# COLLECTIONS
users_collection = db["users"]
messages_collection = db["messages"]
groups_collection = db["groups"]
stories_collection = db["stories"]
contacts_collection = db["contacts"]
