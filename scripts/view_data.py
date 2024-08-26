from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017")

db = client.photo_gallery

photos_collection = db.photos

documents = photos_collection.find()

for document in documents:
    print(document)
