from PIL import Image
from pathlib import Path

def save_image(file, size=(800, 800), path="images/full/"):
    image = Image.open(file)
    image.thumbnail(size)
    full_path = Path(path) / file.filename
    image.save(full_path)
    return str(full_path)

def create_preview(file, size=(150, 150), path="images/preview/"):
    image = Image.open(file)
    image.thumbnail(size)
    preview_path = Path(path) / file.filename
    image.save(preview_path)
    return str(preview_path)