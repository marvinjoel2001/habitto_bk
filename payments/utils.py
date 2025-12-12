import base64
from pathlib import Path
from typing import Optional


def decode_base64_image(data: str) -> bytes:
    """Decodifica una imagen en base64 a bytes."""

    return base64.b64decode(data)


def save_qr_image(qr_base64: str, path: str | Path) -> Path:
    """Guarda un PNG a partir de un string base64 de imagen.

    Args:
        qr_base64: Contenido base64 (sin encabezado data URI).
        path: Ruta destino del archivo PNG.

    Returns:
        Ruta del archivo generado.
    """

    image_bytes = decode_base64_image(qr_base64)
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_bytes(image_bytes)
    return out_path

