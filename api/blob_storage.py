import os
import uuid
import requests

BLOB_API = "https://blob.vercel-storage.com"


def upload_file(file_data, filename):
    token = os.environ.get("BLOB_READ_WRITE_TOKEN")
    if not token:
        raise ValueError("BLOB_READ_WRITE_TOKEN not set")

    ext = filename.rsplit(".", 1)[-1] if "." in filename else "jpg"
    pathname = f"service_photos/{uuid.uuid4().hex}.{ext}"

    resp = requests.put(
        f"{BLOB_API}/{pathname}",
        data=file_data,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/octet-stream",
        },
    )
    resp.raise_for_status()
    data = resp.json()
    return data["url"]


def delete_file(url):
    token = os.environ.get("BLOB_READ_WRITE_TOKEN")
    if not token:
        return

    requests.post(
        f"{BLOB_API}/delete",
        json={"urls": [url]},
        headers={"Authorization": f"Bearer {token}"},
    )
