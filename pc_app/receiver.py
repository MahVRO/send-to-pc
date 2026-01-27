import os
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

def download_file(file_info):
    url = BASE_URL + file_info["url"]
    filename = file_info["filename"]
    path = os.path.join(DOWNLOAD_DIR, filename)

    with requests.get(url, headers=HEADERS, stream=True) as r:
        r.raise_for_status()
        with open(path, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)

    print(f"[✓] File saved: {path}")

def save_text(batch_id, item, index):
    ext = "txt" if item["type"] == "text" else "code"
    path = os.path.join(TEXT_DIR, f"{batch_id}_{index}.{ext}")

    with open(path, "w", encoding="utf-8") as f:
        f.write(item["content"])

    print(f"[✓] {item['type']} saved: {path}")

def process_batches(data):
    print("RAW /pending RESPONSE:")
    print(data)

    batches = data.get("batches", [])
    if not batches:
        print("No pending batches.")
        return

    for batch in batches:
        print("BATCH OBJECT:", batch)

        batch_id = batch["batch_id"]
        print(f"[!] Batch {batch_id} processed")
        ack_batch(batch_id)

        for i, item in enumerate(batch.get("items", [])):
            save_text(batch_id, item, i)

        for file in batch.get("files", []):
            download_file(file)

def main():
    ensure_dirs()
    data = get_pending()
    process_batches(data)

if __name__ == "__main__":
    main()

def ack_batch(batch_id):
    r = requests.post(f"{BASE_URL}/ack/{batch_id}", headers=HEADERS, timeout=10)
    r.raise_for_status()
    print(f"[✓] Batch {batch_id} acknowledged")
