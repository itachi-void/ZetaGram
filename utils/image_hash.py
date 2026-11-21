import io
from PIL import Image


def compute_dhash(image_bytes: bytes, hash_size: int = 8) -> str:
    """Compute a 64-bit difference hash (dHash) hex string from raw image bytes."""
    with Image.open(io.BytesIO(image_bytes)) as img:
        gray = img.convert("L").resize((hash_size + 1, hash_size), Image.Resampling.LANCZOS)
        pixels = list(gray.get_flattened_data()) if hasattr(gray, "get_flattened_data") else list(gray.getdata())
        bits = 0
        for row in range(hash_size):
            row_start = row * (hash_size + 1)
            for col in range(hash_size):
                bits = (bits << 1) | (1 if pixels[row_start + col] > pixels[row_start + col + 1] else 0)
        width = (hash_size * hash_size) // 4
        return f"{bits:0{width}x}"


def hamming_distance(h1: str, h2: str) -> int:
    """Return Hamming distance between two hex dHash strings."""
    return (int(h1, 16) ^ int(h2, 16)).bit_count()


def is_similar_hash(h1: str | None, h2: str | None, max_distance: int = 6) -> bool:
    """Return True if both hashes are present and within max_distance Hamming bits."""
    if not h1 or not h2 or len(h1) != len(h2):
        return False
    try:
        return hamming_distance(h1, h2) <= max_distance
    except ValueError:
        return False
