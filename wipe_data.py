from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017")
db = client.photo_gallery
photos_collection = db.photos

result = photos_collection.delete_many({})

print(f"Deleted {result.deleted_count} documents.")
