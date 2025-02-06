from PIL import Image
import io
import cv2


def compress_image(image_data, quality=50):
    """Compress image using JPEG format to reduce size."""
    image = Image.open(io.BytesIO(image_data))  # Load image from bytes
    buffer = io.BytesIO()
    image.save(buffer, format="JPEG", quality=quality)  # Save compressed
    return buffer.getvalue()