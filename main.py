import os
from io import BytesIO

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import StreamingResponse
from PIL import Image

app = FastAPI(title="Omagine Background Removal API")

ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png", "image/webp"}
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
MAX_IMAGE_SIZE = 10 * 1024 * 1024


def remove_background_bytes(image_data: bytes) -> bytes:
    os.environ.setdefault("NUMBA_DISABLE_JIT", "1")
    from rembg import remove

    return remove(image_data)


def validate_image_upload(file: UploadFile, image_data: bytes):
    if not file.filename:
        raise HTTPException(status_code=400, detail="Image file is required")

    _, extension = os.path.splitext(file.filename.lower())
    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail="Unsupported file extension. Use jpg, jpeg, png, or webp",
        )

    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=400,
            detail="Unsupported content type. Upload a jpg, png, or webp image",
        )

    if not image_data:
        raise HTTPException(status_code=400, detail="Uploaded image is empty")

    if len(image_data) > MAX_IMAGE_SIZE:
        raise HTTPException(status_code=413, detail="Image must be 10MB or smaller")

    try:
        with Image.open(BytesIO(image_data)) as image:
            image.verify()
    except Exception:
        raise HTTPException(status_code=400, detail="Uploaded file is not a valid image")


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.post("/remove-bg")
async def remove_bg(file: UploadFile = File(...)):
    image_data = await file.read()
    validate_image_upload(file, image_data)

    try:
        output_data = remove_background_bytes(image_data)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to remove image background: {str(e)}",
        )

    output_filename = os.path.splitext(file.filename)[0] + "-no-bg.png"
    return StreamingResponse(
        BytesIO(output_data),
        media_type="image/png",
        headers={"Content-Disposition": f'attachment; filename="{output_filename}"'},
    )
