import base64
import time
from typing import Tuple
import cv2
import numpy as np

def b64_to_bgr(image_b64: str) -> np.ndarray:
    raw = base64.b64decode(image_b64)
    arr = np.frombuffer(raw, dtype=np.uint8)
    img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if img is None:
        raise ValueError("Failed to decode image")
    return img

def bgr_to_b64(img: np.ndarray, ext: str = ".jpg", quality: int = 85) -> str:
    params = []
    if ext.lower() in [".jpg", ".jpeg"]:
        params = [int(cv2.IMWRITE_JPEG_QUALITY), int(quality)]
    ok, buf = cv2.imencode(ext, img, params)
    if not ok:
        raise ValueError("Failed to encode image")
    return base64.b64encode(buf.tobytes()).decode("ascii")

def blur_faces(img: np.ndarray) -> np.ndarray:
    # Uses OpenCV bundled Haar cascade path; no extra file needed.
    cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
    face_cascade = cv2.CascadeClassifier(cascade_path)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray, 1.2, 5)
    out = img.copy()
    for (x, y, w, h) in faces:
        roi = out[y:y+h, x:x+w]
        roi = cv2.GaussianBlur(roi, (31, 31), 0)
        out[y:y+h, x:x+w] = roi
    return out

def downscale(img: np.ndarray, max_side: int = 960) -> np.ndarray:
    h, w = img.shape[:2]
    m = max(h, w)
    if m <= max_side:
        return img
    scale = max_side / float(m)
    return cv2.resize(img, (int(w*scale), int(h*scale)), interpolation=cv2.INTER_AREA)

def preprocess(image_b64: str, enable_face_blur: bool = True) -> Tuple[np.ndarray, float]:
    t0 = time.perf_counter()
    img = b64_to_bgr(image_b64)
    img = downscale(img)
    if enable_face_blur:
        img = blur_faces(img)
    t_ms = (time.perf_counter() - t0) * 1000.0
    return img, t_ms
