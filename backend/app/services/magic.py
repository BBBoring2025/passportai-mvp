"""Magic bytes validator — checks file content matches claimed MIME type."""

# Magic byte signatures
_SIGNATURES: dict[str, list[bytes]] = {
    "application/pdf": [b"%PDF"],
    "image/jpeg": [b"\xff\xd8\xff"],
    "image/png": [b"\x89PNG\r\n\x1a\n"],
}


def validate_magic_bytes(file_bytes: bytes, claimed_mime: str) -> bool:
    """
    Validate that file content matches its claimed MIME type by checking magic bytes.

    Returns True if the magic bytes match the claimed MIME type.
    Returns True for unknown MIME types (fail-open for extensibility).
    Returns False if file is too short or magic bytes don't match.
    """
    if not file_bytes:
        return False

    signatures = _SIGNATURES.get(claimed_mime)
    if signatures is None:
        # Unknown MIME type — fail open (not our concern)
        return True

    for sig in signatures:
        if file_bytes[: len(sig)] == sig:
            return True

    return False
