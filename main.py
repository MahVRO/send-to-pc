from fastapi import FastAPI, UploadFile, File, HTTPException, Request, Form, requests
from fastapi.middleware.cors import CORSMiddleware
import os, uuid, json

APP_TOKEN = "9f8a1d3c4e6b7a2f8c9d0e1a2b3c4d5e153uoi135e7f8a9b0c1d2e3f4g5h6i7j"
UPLOAD_DIR = "server/uploads"
MAX_FILE_SIZE = 100 * 1024 * 1024

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

os.makedirs(UPLOAD_DIR, exist_ok=True)

pending_items = []


def require_token(request: Request):
    auth = request.headers.get("authorization")
    if auth != f"Bearer {APP_TOKEN}":
        raise HTTPException(status_code=403, detail="Invalid token")

from fastapi.responses import JSONResponse

@app.get("/pending")
def get_pending(request: Request):
    auth = request.headers.get("Authorization")
    if auth != f"Bearer {APP_TOKEN}":
        raise HTTPException(status_code=401, detail="Unauthorized")

    return {
        "batches": pending_items
    }

@app.options("/send")
async def options_send():
    return JSONResponse(status_code=200)

@app.post("/send")
async def send(
    request: Request,
    meta: str = Form(...),
    files: list[UploadFile] | None = File(None),
):

    require_token(request)

    try:
        data = json.loads(meta)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid meta")

    total = 0
    saved_files = []

    for f in files:
        contents = await f.read()
        total += len(contents)
        if total > MAX_FILE_SIZE:
            raise HTTPException(status_code=413, detail="Too large")

        fid = str(uuid.uuid4())
        path = os.path.join(UPLOAD_DIR, f"{fid}_{f.filename}")
        with open(path, "wb") as out:
            out.write(contents)

        saved_files.append({
            "name": f.filename,
            "path": path,
            "size": len(contents)
        })

    pending_items.append({
        "id": str(uuid.uuid4()),
        "items": data["items"],
        "files": saved_files
    })

    return {"ok": True}
