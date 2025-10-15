from __future__ import annotations

import json
import logging
import os
from collections import defaultdict
from dataclasses import dataclass
from hashlib import md5
from pathlib import Path
from typing import Callable, Dict, Iterable, List, Optional, Sequence

from PIL import Image

from .models import CarImage
from .parser import parse_filename

LOGGER = logging.getLogger(__name__)

CACHE_FILENAME = "index.json"
THUMBNAIL_EXT = ".jpg"


def _iter_image_paths(data_dir: Path) -> Iterable[Path]:
    patterns = ("*.jpg", "*.jpeg", "*.png")
    for pattern in patterns:
        yield from data_dir.rglob(pattern)


def _compute_digest(paths: Sequence[Path]) -> str:
    hasher = md5()
    for path in sorted(paths):
        try:
            stat = path.stat()
        except FileNotFoundError:
            continue
        entry = f"{path}:{int(stat.st_mtime_ns)}:{stat.st_size}"
        hasher.update(entry.encode("utf-8"))
    return hasher.hexdigest()


@dataclass
class DatasetIndex:
    """In-memory dataset index with helper lookup structures."""

    records: List[CarImage]
    cache_dir: Path
    thumb_dir: Path
    by_make: Dict[str, List[CarImage]]
    by_make_model: Dict[tuple[str, str], List[CarImage]]

    def __post_init__(self) -> None:
        self.thumb_dir.mkdir(parents=True, exist_ok=True)

    def ensure_thumbnail(self, car: CarImage, size: int = 512) -> Path:
        """Return thumbnail path, generating it if necessary."""
        thumb_name = f"{car.id}{THUMBNAIL_EXT}"
        thumb_path = self.thumb_dir / thumb_name

        if thumb_path.exists():
            return thumb_path

        try:
            with Image.open(car.path) as img:
                img = img.convert("RGB")
                img.thumbnail((size, size), Image.Resampling.LANCZOS)
                thumb_path.parent.mkdir(parents=True, exist_ok=True)
                img.save(thumb_path, format="JPEG", quality=90)
        except Exception as exc:  # pragma: no cover - depends on external files
            LOGGER.warning("Failed to build thumbnail for %s: %s", car.path, exc)
            return car.path

        return thumb_path

    def to_json_serializable(self, digest: str) -> Dict:
        return {
            "version": 1,
            "digest": digest,
            "records": [
                {
                    "id": car.id,
                    "path": str(car.path),
                    "make": car.make,
                    "model": car.model,
                    "year": car.year,
                    "random_id": car.random_id,
                    "specs": car.specs,
                }
                for car in self.records
            ],
        }

    def get_random_pool(self) -> List[CarImage]:
        """Return all records for sampling."""
        return self.records

    def get_by_make(self, make: str) -> List[CarImage]:
        return self.by_make.get(make, [])

    def get_by_make_model(self, make: str, model: str) -> List[CarImage]:
        return self.by_make_model.get((make, model), [])


def load_index(
    data_dir: Path,
    cache_dir: Path,
    thumb_dir: Path,
    force_rebuild: bool = False,
    progress_callback: Optional[Callable[[int, int], None]] = None,
) -> DatasetIndex:
    """
    Load the dataset index from cache, rebuilding if necessary.

    progress_callback(current, total) can be provided for UI updates.
    """
    cache_dir.mkdir(parents=True, exist_ok=True)
    thumb_dir.mkdir(parents=True, exist_ok=True)

    image_paths = list(_iter_image_paths(data_dir))
    if not image_paths:
        raise FileNotFoundError(f"No images found in {data_dir}")

    digest = _compute_digest(image_paths)
    cache_file = cache_dir / CACHE_FILENAME

    if not force_rebuild and cache_file.exists():
        try:
            with cache_file.open("r", encoding="utf-8") as fh:
                payload = json.load(fh)
            if payload.get("version") == 1 and payload.get("digest") == digest:
                records = [
                    CarImage(
                        id=entry["id"],
                        path=Path(entry["path"]),
                        make=entry["make"],
                        model=entry["model"],
                        year=int(entry["year"]),
                        random_id=entry.get("random_id", ""),
                        specs=entry.get("specs", {}),
                    )
                    for entry in payload.get("records", [])
                ]
                if records:
                    LOGGER.info("Loaded dataset index from cache (%s entries).", len(records))
                    return _build_dataset_index(records, cache_dir, thumb_dir)
        except Exception as exc:  # pragma: no cover - reading cache failure
            LOGGER.warning("Failed to load cache, rebuilding index: %s", exc)

    LOGGER.info("Building dataset index from %s images.", len(image_paths))
    records: List[CarImage] = []

    for idx, path in enumerate(image_paths, start=1):
        car = parse_filename(path)
        if car:
            records.append(car)
        if progress_callback:
            progress_callback(idx, len(image_paths))

    if not records:
        raise RuntimeError("No valid car images found after parsing filenames.")

    dataset = _build_dataset_index(records, cache_dir, thumb_dir)

    serializable = dataset.to_json_serializable(digest)
    with (cache_dir / CACHE_FILENAME).open("w", encoding="utf-8") as fh:
        json.dump(serializable, fh, indent=2)

    LOGGER.info("Dataset index built with %s entries.", len(records))
    return dataset


def _build_dataset_index(records: List[CarImage], cache_dir: Path, thumb_dir: Path) -> DatasetIndex:
    by_make: Dict[str, List[CarImage]] = defaultdict(list)
    by_make_model: Dict[tuple[str, str], List[CarImage]] = defaultdict(list)

    for record in records:
        by_make[record.make].append(record)
        by_make_model[(record.make, record.model)].append(record)

    return DatasetIndex(
        records=records,
        cache_dir=cache_dir,
        thumb_dir=thumb_dir,
        by_make=dict(by_make),
        by_make_model=dict(by_make_model),
    )
