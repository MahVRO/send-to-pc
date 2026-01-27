import os
import re
import requests
from config import BASE_URL, APP_TOKEN, DOWNLOAD_DIR, TEXT_DIR

HEADERS = {
    "Authorization": f"Bearer {APP_TOKEN}"
}

def ensure_dirs():
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    os.makedirs(TEXT_DIR, exist_ok=True)

def get_pending():
    r = requests.get(f"{BASE_URL}/pending", headers=HEADERS, timeout=10)
    r.raise_for_status()
    return r.json()

def _sanitize_filename(name: str) -> str:
    """Remove dangerous characters and normalize filename."""
    name = os.path.basename(name)
    return re.sub(r"[^A-Za-z0-9._-]", "_", name)

def _resolve_collision(path: str) -> str:
    """If file exists, append an incrementing suffix."""
    if not os.path.exists(path):
        return path
    base, ext = os.path.splitext(path)
    i = 1
    while True:
        candidate = f"{base}_{i}{ext}"
        if not os.path.exists(candidate):
            return candidate
        i += 1

def download_file(file_info):
    url = BASE_URL + file_info.get("url", "")
    raw_name = file_info.get("filename", "file")
    filename = _sanitize_filename(raw_name)
    path = _resolve_collision(os.path.join(DOWNLOAD_DIR, filename))

    with requests.get(url, headers=HEADERS, stream=True) as r:
        r.raise_for_status()
        with open(path, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)

    print(f"[✓] File saved: {path}")

def save_text(batch_id, item, index):
    ext = "txt" if item.get("type") == "text" else "code"
    filename = f"{batch_id}_{index}.{ext}"
    path = _resolve_collision(os.path.join(TEXT_DIR, filename))

    with open(path, "w", encoding="utf-8") as f:
        f.write(item.get("content", ""))

    print(f"[✓] {item.get('type', 'unknown')} saved: {path}")

def ack_batch(batch_id):
    r = requests.post(f"{BASE_URL}/ack/{batch_id}", headers=HEADERS, timeout=10)
    r.raise_for_status()
    print(f"[✓] Batch {batch_id} acknowledged")

def process_batches(data):
    batches = data.get("batches", [])
    if not batches:
        print("No pending batches.")
        return

    for batch in batches:
        batch_id = batch.get("batch_id") or batch.get("id")
        if not batch_id:
            print("[!] Skipping batch without identifier:", batch)
            continue

        print(f"\n=== Batch {batch_id} ===")

        success = True
        try:
            for i, item in enumerate(batch.get("items", [])):
                save_text(batch_id, item, i)

            for file in batch.get("files", []):
                download_file(file)
        except Exception as e:
            success = False
            print(f"[!] Error while processing batch {batch_id}: {e}")

        if success:
            ack_batch(batch_id)
        else:
            print(f"[!] Batch {batch_id} not acknowledged due to errors")

def main():
    ensure_dirs()
    data = get_pending()
    process_batches(data)

if __name__ == "__main__":
    main()
