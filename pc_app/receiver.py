import os
import re
import requests
from config import BASE_URL, APP_TOKEN, DOWNLOAD_DIR, TEXT_DIR

HEADERS = {
    "Authorization": f"Bearer {APP_TOKEN}"
}

DELETED_DIR = os.path.join(os.path.dirname(DOWNLOAD_DIR), "deleted")

# =============================
# Low-level helpers
# =============================

def ensure_dirs():
    os.makedirs(DELETED_DIR, exist_ok=True)
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    os.makedirs(TEXT_DIR, exist_ok=True)


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

# =============================
# API layer (UI-safe)
# =============================

def fetch_pending_batches():
    """
    Returns a list of batches without side effects.
    Safe to call from a UI.
    """
    r = requests.get(f"{BASE_URL}/pending", headers=HEADERS, timeout=10)
    r.raise_for_status()
    data = r.json()
    return data.get("batches", [])


def accept_batch(batch: dict, deleted_item_indexes: set[int] | None = None):
    """
    Accepts a batch with optional filtering:
    - non-deleted items are saved normally
    - deleted items are routed to received/deleted
    - ACKs on success
    """
    """
    Accepts a batch:
    - saves text
    - downloads files
    - ACKs on success
    """
    ensure_dirs()

    batch_id = batch.get("id") or batch.get("batch_id")
    if not batch_id:
        raise ValueError("Batch has no identifier")

    # Save text items
    for i, item in enumerate(batch.get("items", [])):
        ext = "txt" if item.get("type") == "text" else "code"
        filename = f"{batch_id}_{i}.{ext}"
        is_deleted = deleted_item_indexes and i in deleted_item_indexes
        base_dir = DELETED_DIR if is_deleted else TEXT_DIR
        path = _resolve_collision(os.path.join(base_dir, filename))

        content = item.get("content")
        if content is None:
            content = ""

        with open(path, "w", encoding="utf-8") as f:
            f.write(content)

    # Download files

    for j, file_info in enumerate(batch.get("files", [])):
        idx = j + len(batch.get("items", []))
        is_deleted = deleted_item_indexes and idx in deleted_item_indexes
        url = BASE_URL + file_info.get("url", "")
        raw_name = file_info.get("filename", "file")
        filename = _sanitize_filename(raw_name)
        base_dir = DELETED_DIR if is_deleted else DOWNLOAD_DIR
        path = _resolve_collision(os.path.join(base_dir, filename))

        with requests.get(url, headers=HEADERS, stream=True) as r:
            r.raise_for_status()
            with open(path, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)

    # ACK only after success
    r = requests.post(f"{BASE_URL}/ack/{batch_id}", headers=HEADERS, timeout=10)
    r.raise_for_status()

    return batch_id

# =============================
# CLI entry (temporary)
# =============================

def main():
    batches = fetch_pending_batches()
    if not batches:
        print("No pending batches.")
        return

    for batch in batches:
        bid = accept_batch(batch)
        print(f"[✓] Batch {bid} accepted")


if __name__ == "__main__":
    main()
