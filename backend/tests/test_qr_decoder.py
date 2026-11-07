from io import BytesIO

import pytest
from PIL import Image

from app.services.qr_decoder import QRDecodeError, decode_qr_image


def test_decoder_rejects_empty_upload():
    with pytest.raises(QRDecodeError, match="empty"):
        decode_qr_image(b"")


def test_decoder_rejects_non_image_upload():
    with pytest.raises(QRDecodeError, match="supported image"):
        decode_qr_image(b"not-an-image")


def test_decoder_rejects_image_without_qr_code():
    output = BytesIO()
    Image.new("RGB", (100, 100), "white").save(output, format="PNG")
    with pytest.raises(QRDecodeError, match="No readable QR code"):
        decode_qr_image(output.getvalue())
