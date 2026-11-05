"""Decode QR image bytes without opening decoded destinations."""
from io import BytesIO

import cv2
import numpy as np
from PIL import Image, UnidentifiedImageError
from pyzbar.pyzbar import ZBarSymbol, decode


class QRDecodeError(ValueError):
    pass


def decode_qr_image(image_bytes: bytes) -> list[dict[str, str]]:
    if not image_bytes:
        raise QRDecodeError("The uploaded file is empty.")
    try:
        with Image.open(BytesIO(image_bytes)) as image:
            image.verify()
        with Image.open(BytesIO(image_bytes)) as image:
            frame = cv2.cvtColor(np.array(image.convert("RGB")), cv2.COLOR_RGB2BGR)
    except (UnidentifiedImageError, OSError, ValueError) as exc:
        raise QRDecodeError("The file is not a supported image.") from exc

    items = decode(frame, symbols=[ZBarSymbol.QRCODE])
    results = []
    for item in items:
        payload = item.data.decode("utf-8", errors="replace")
        results.append({"payload": payload, "format": "QR_CODE"})
    if not results:
        raise QRDecodeError("No readable QR code was found in this image.")
    return results
