import os
from io import BytesIO

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from PIL import Image

app = FastAPI(title="Omagine Background Removal API")

CORS_ALLOWED_ORIGINS = [
"https://omagine.app",
"https://backend.omagine.app",
"https://localhost:8000",
"https://localhost:3000",
"https://localhost:3001",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ALLOWED_ORIGINS,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
    return {"status": "Healthy"}


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
