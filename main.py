from fastapi import FastAPI, UploadFile, File
from fastapi.responses import StreamingResponse
from rembg import remove
from PIL import Image
import io

app = FastAPI()

@app.get("/")
def read_root():
    return {"status": "Omagine service running"}

@app.post("/remove-bg")
async def remove_bg(file: UploadFile = File(...)):
    image = Image.open(io.BytesIO(await file.read())).convert("RGBA")
    output = remove(image)

    buf = io.BytesIO()
    output.save(buf, format="PNG")
    buf.seek(0)

    return StreamingResponse(buf, media_type="image/png")