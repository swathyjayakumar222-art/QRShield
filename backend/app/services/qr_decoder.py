"""Decode QR image bytes using OpenCV without opening decoded destinations."""
from io import BytesIO

import cv2
import numpy as np
from PIL import Image, UnidentifiedImageError

MAX_IMAGE_PIXELS = 25_000_000


class QRDecodeError(ValueError):
    pass


def decode_qr_image(image_bytes: bytes) -> list[dict[str, str]]:
    if not image_bytes:
        raise QRDecodeError("The uploaded file is empty.")
    try:
        with Image.open(BytesIO(image_bytes)) as image:
            if image.width * image.height > MAX_IMAGE_PIXELS:
                raise QRDecodeError("Image dimensions exceed the 25-megapixel limit.")
            image.verify()
        with Image.open(BytesIO(image_bytes)) as image:
            if image.width * image.height > MAX_IMAGE_PIXELS:
                raise QRDecodeError("Image dimensions exceed the 25-megapixel limit.")
            frame = cv2.cvtColor(np.array(image.convert("RGB")), cv2.COLOR_RGB2BGR)
    except QRDecodeError:
        raise
    except (UnidentifiedImageError, OSError, ValueError, Image.DecompressionBombError) as exc:
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
