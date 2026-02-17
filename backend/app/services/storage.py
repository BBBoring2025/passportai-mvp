import hashlib
import uuid
from pathlib import Path

from app.config import settings

BUCKET_NAME = "documents"


def _supabase_configured() -> bool:
    return bool(settings.supabase_url and settings.supabase_service_key)


def compute_sha256(file_bytes: bytes) -> str:
    return hashlib.sha256(file_bytes).hexdigest()


def upload_file(
    file_bytes: bytes,
    filename: str,
    case_id: uuid.UUID,
    document_id: uuid.UUID,
    mime_type: str,
) -> str:
    """Upload file to storage. Returns the storage_path."""
    storage_key = f"cases/{case_id}/{document_id}/{filename}"

    if _supabase_configured():
        return _upload_supabase(file_bytes, storage_key, mime_type)
    return _upload_local(file_bytes, storage_key)


def _upload_supabase(file_bytes: bytes, storage_key: str, mime_type: str) -> str:
    import httpx

    url = f"{settings.supabase_url}/storage/v1/object/{BUCKET_NAME}/{storage_key}"
    headers = {
        "apikey": settings.supabase_service_key,
        "Authorization": f"Bearer {settings.supabase_service_key}",
        "Content-Type": mime_type,
        "x-upsert": "true",
    }
    response = httpx.post(url, content=file_bytes, headers=headers)
    response.raise_for_status()
    return f"{BUCKET_NAME}/{storage_key}"


def _upload_local(file_bytes: bytes, storage_key: str) -> str:
    upload_dir = Path(settings.upload_dir)
    file_path = upload_dir / storage_key
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_bytes(file_bytes)
    return str(file_path)


def get_file_bytes(storage_path: str) -> bytes:
    """Retrieve file bytes from storage."""
    if _supabase_configured() and storage_path.startswith(BUCKET_NAME):
        return _download_supabase(storage_path)
    return Path(storage_path).read_bytes()


def _download_supabase(storage_path: str) -> bytes:
    import httpx

    url = f"{settings.supabase_url}/storage/v1/object/{storage_path}"
    headers = {
        "apikey": settings.supabase_service_key,
        "Authorization": f"Bearer {settings.supabase_service_key}",
    }
    response = httpx.get(url, headers=headers)
    response.raise_for_status()
    return response.content
