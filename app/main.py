from fastapi import FastAPI, UploadFile, File, HTTPException
from pymongo import MongoClient
import os
import uuid
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware

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

os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.post("/upload/")
async def upload_photo(file: UploadFile = File(...)):
    file_id = str(uuid.uuid4())
    file_path = os.path.join(UPLOAD_DIR, file_id + "-" + file.filename)

    with open(file_path, "wb") as buffer:
        buffer.write(await file.read())

    photo_data = {
        "file_id": file_id,
        "filename": file.filename,
        "filepath": file_path,
    }
    result = photos_collection.insert_one(photo_data)

    if result.acknowledged:
        return {"file_id": file_id, "filename": file.filename}
    else:
        raise HTTPException(status_code=500, detail="File upload failed")

@app.get("/images/previews")
async def get_image_previews():
    print('getting image previews...')
    images = photos_collection.find({}, {"_id": 0, "file_id": 1, "filename": 1})
    print('images', images)
    return list(images)

@app.get("/images/{file_id}/preview")
async def get_image_preview(file_id: str):
    print('get image preview')
    image = photos_collection.find_one({"file_id": file_id})
    print('found image', image)
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")

    return FileResponse(image["filepath"])

@app.get("/images/{file_id}/full")
async def get_full_image(file_id: str):
    image = photos_collection.find_one({"file_id": file_id})
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")

    return FileResponse(image["filepath"])