from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017")

db = client.photo_gallery

photos_collection = db.photos

def approve_all_images():
    result = photos_collection.update_many(
        {},
        {"$set": {"approved": True}}
    )
    return {"message": f"Approved {result.modified_count} images."}

print(approve_all_images())