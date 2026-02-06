import os
from simulation.load.dataset_adapter import frames_from_folder

def _smart_folder(base: str, candidates: list[str]) -> str:
    for c in candidates:
        p = os.path.join(base, c)
        if os.path.isdir(p):
            return p
    return base

def kaggle_peoplecounting_frames(base: str, max_n: int = 200):
    p = _smart_folder(base, ["images", "Images", "imgs", "Img", "data"])
    yield from frames_from_folder(p, sensor_id="kaggle-peoplecounting", max_n=max_n)

def kaggle_human_detection_cctv_frames(base: str, max_n: int = 200):
    p = _smart_folder(base, ["images", "Images", "data"])
    yield from frames_from_folder(p, sensor_id="kaggle-human-detection-cctv", max_n=max_n)

def kaggle_fire_dataset_frames(base: str, max_n: int = 200):
    found = False
    for cls in ["fire_images", "non_fire_images", "non-fire_images", "fire", "non_fire", "non-fire"]:
        p = os.path.join(base, cls)
        if os.path.isdir(p):
            found = True
            yield from frames_from_folder(p, sensor_id=f"kaggle-fire-{cls}", max_n=max_n)
    if not found:
        yield from frames_from_folder(base, sensor_id="kaggle-fire-fallback", max_n=max_n)

def kaggle_floodnet_frames(base: str, max_n: int = 200):
    p = _smart_folder(base, ["Images", "images", "image", "imgs", "JPEGImages"])
    yield from frames_from_folder(p, sensor_id="kaggle-floodnet", max_n=max_n)

def kaggle_disaster_damage_5class_frames(base: str, max_n: int = 200):
    yield from frames_from_folder(base, sensor_id="kaggle-disaster-damage-5class", max_n=max_n)

def kaggle_archive3_frames(base: str, max_n: int = 200):
    yield from frames_from_folder(base, sensor_id="kaggle-archive3", max_n=max_n)

