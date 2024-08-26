from fastapi import FastAPI, UploadFile, File, Form, HTTPException
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
async def upload_photo(
    file: UploadFile = File(...),
    email: str = Form(...),
    name: str = Form(...),
    photo_context: str = Form(...),
    tags: str = Form(...)
):

    toronto_tz = pytz.timezone('America/Toronto')
    upload_time = datetime.now(toronto_tz)

    file_id = str(uuid.uuid4())
    file_path = os.path.join(UPLOAD_DIR, file_id + "-" + file.filename)
    preview_path = os.path.join(PREVIEW_DIR, file_id + "-" + file.filename)

    with open(file_path, "wb") as buffer:
        buffer.write(await file.read())

    preview_width, preview_height = create_preview(file_path, preview_path)

    with Image.open(file_path) as img:
        full_width, full_height = img.width, img.height

    tags_list = tags.split(',')

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
        "upload_time": upload_time
    }
    result = photos_collection.insert_one(photo_data)

    if result.acknowledged:
        return {"file_id": file_id, "filename": file.filename}
    else:
        raise HTTPException(status_code=500, detail="File upload failed")

@app.get("/images/previews")
async def get_image_previews():
    images = list(photos_collection.find({}, {"_id": 0}))
    
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
