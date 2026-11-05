"""Decode QR image bytes using OpenCV without opening destinations."""
from io import BytesIO

import cv2
import numpy as np
from PIL import Image, UnidentifiedImageError


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

    detector = cv2.QRCodeDetector()
    payload, points, _ = detector.detectAndDecode(frame)
    if payload and points is not None:
        return [{"payload": payload, "format": "QR_CODE"}]

    if hasattr(detector, "detectAndDecodeMulti"):
        ok, decoded_info, _, _ = detector.detectAndDecodeMulti(frame)
        if ok:
            values = [value for value in decoded_info if value]
            if values:
                return [{"payload": value, "format": "QR_CODE"} for value in values]

    raise QRDecodeError("No readable QR code was found in this image.")
