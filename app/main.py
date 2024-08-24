from fastapi import FastAPI, UploadFile, File, HTTPException
from pymongo import MongoClient
import os
import uuid
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from PIL import Image

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

@app.post("/upload/")
async def upload_photo(file: UploadFile = File(...)):
    file_id = str(uuid.uuid4())
    file_path = os.path.join(UPLOAD_DIR, file_id + "-" + file.filename)
    preview_path = os.path.join(PREVIEW_DIR, file_id + "-" + file.filename)

    with open(file_path, "wb") as buffer:
        buffer.write(await file.read())

    create_preview(file_path, preview_path)

    photo_data = {
        "file_id": file_id,
        "filename": file.filename,
    }
    result = photos_collection.insert_one(photo_data)

    if result.acknowledged:
        return {"file_id": file_id, "filename": file.filename}
    else:
        raise HTTPException(status_code=500, detail="File upload failed")

@app.get("/images/previews")
async def get_image_previews():
    images = photos_collection.find({}, {"_id": 0, "file_id": 1, "filename": 1})
    return list(images)

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
