from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Depends
from pymongo import MongoClient
import os
import uuid
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from PIL import Image
from datetime import datetime
import pytz
from collections import defaultdict

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

client = MongoClient("mongodb://localhost:27017")
db = client.photo_gallery
photos_collection = db.photos

UPLOAD_DIR = "uploads/"
PREVIEW_DIR = "previews/"

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(PREVIEW_DIR, exist_ok=True)

def create_preview(image_path, preview_path, height=400):
    with Image.open(image_path) as img:
        aspect_ratio = img.width / img.height
        new_width = int(height * aspect_ratio)
        img = img.resize((new_width, height), Image.LANCZOS)
        img.save(preview_path)
        return img.width, img.height

@app.post("/upload/")
async def upload_photos(
    files: list[UploadFile] = File(...),
    email: str = Form(...),
    name: str = Form(...),
    photo_context: str = Form(...),
    tags: str = Form(...)
):

    toronto_tz = pytz.timezone('America/Toronto')
    upload_time = datetime.now(toronto_tz)
    tags_list = tags.split(',')

    photo_data_list = []

    for file in files:
        file_id = str(uuid.uuid4())
        file_path = os.path.join(UPLOAD_DIR, file_id + "-" + file.filename)
        preview_path = os.path.join(PREVIEW_DIR, file_id + "-" + file.filename)

        with open(file_path, "wb") as buffer:
            buffer.write(await file.read())

        preview_width, preview_height = create_preview(file_path, preview_path)

        with Image.open(file_path) as img:
            full_width, full_height = img.width, img.height

        photo_data = {
            "file_id": file_id,
            "filename": file.filename,
            "email": email,
            "name": name,
            "photo_context": photo_context,
            "tags": tags_list,
            "full_width": full_width,
            "full_height": full_height,
            "preview_width": preview_width,
            "preview_height": preview_height,
            "upload_time": upload_time,
            "approved": False
        }
        photo_data_list.append(photo_data)

    result = photos_collection.insert_many(photo_data_list)

    if result.acknowledged:
        return {"uploaded_files": [photo["file_id"] for photo in photo_data_list]}
    else:
        raise HTTPException(status_code=500, detail="File upload failed")

@app.get("/images/previews")
async def get_image_previews():
    images = list(photos_collection.find({"approved": True}, {"_id": 0}))

    grouped_images = defaultdict(list)
    for image in images:
        upload_date = image["upload_time"].date().isoformat()
        grouped_images[upload_date].append(image)

    sorted_grouped_images = sorted(grouped_images.items(), reverse=True)

    for date, images in sorted_grouped_images:
        images.sort(key=lambda x: x["upload_time"], reverse=True)

    return sorted_grouped_images

@app.get("/images/{file_id}/preview")
async def get_image_preview(file_id: str):
    image = photos_collection.find_one({"file_id": file_id})
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")

    preview_path = os.path.join(PREVIEW_DIR, image["file_id"] + "-" + image["filename"])
    return FileResponse(preview_path)

@app.get("/images/{file_id}/full")
async def get_full_image(file_id: str):
    image = photos_collection.find_one({"file_id": file_id})
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")

    file_path = os.path.join(UPLOAD_DIR, image["file_id"] + "-" + image["filename"])
    return FileResponse(file_path)

@app.post("/images/{file_id}/approve")
async def approve_photo(file_id: str):
    result = photos_collection.update_one(
        {"file_id": file_id},
        {"$set": {"approved": True}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Image not found")
    return {"message": "Photo approved successfully"}

@app.get("/images/unapproved")
async def get_unapproved_images():
    images = list(photos_collection.find({"approved": False}, {"_id": 0}))
    return images