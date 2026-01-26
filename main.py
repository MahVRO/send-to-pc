from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
import os
import uuid

APP_TOKEN = "9f8a1d3c4e6b7a2f8c9d0e1a2b3c4d5e153uoi135e7f8a9b0c1d2e3f4g5h6i7j"
UPLOAD_DIR = "server/uploads"
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100 MB

app = FastAPI()

os.makedirs(UPLOAD_DIR, exist_ok=True)

pending_items = []


@app.post("/send")
async def send_file(token: str, file: UploadFile = File(...)):
    if token != APP_TOKEN:
        raise HTTPException(status_code=403, detail="Invalid token")

    contents = await file.read()
    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="File too large")

    file_id = str(uuid.uuid4())
    file_path = os.path.join(UPLOAD_DIR, f"{file_id}_{file.filename}")

    with open(file_path, "wb") as f:
        f.write(contents)

    pending_items.append({
        "id": file_id,
        "filename": file.filename,
        "path": file_path
    })

    return {"status": "sent", "id": file_id}


@app.get("/pending")
def get_pending(token: str):
    if token != APP_TOKEN:
        raise HTTPException(status_code=403, detail="Invalid token")
    return pending_items
