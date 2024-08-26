from pymongo import MongoClient
import os

client = MongoClient("mongodb://localhost:27017")
db = client.photo_gallery
photos_collection = db.photos

UPLOAD_DIR = "uploads/"
PREVIEW_DIR = "previews/"

result = photos_collection.delete_many({})

print(f"Deleted {result.deleted_count} documents.")

def delete_all_images(directory):
    for filename in os.listdir(directory):
        file_path = os.path.join(directory, filename)
        try:
            os.remove(file_path)
        except Exception as e:
            print(f"Failed to delete {file_path}. Reason: {e}")

delete_all_images(UPLOAD_DIR)
delete_all_images(PREVIEW_DIR)

print("Deleted all images.")
