from __future__ import annotations

import logging
from pathlib import Path
from typing import Dict, List, Optional

from .models import CarImage

LOGGER = logging.getLogger(__name__)

SPEC_KEYS: List[str] = [
    "make",
    "model",
    "year",
    "msrp",
    "front_wheel_size_in",
    "sae_net_hp_rpm",
    "displacement",
    "engine_type",
    "width_in",
    "height_in",
    "length_in",
    "gas_mileage",
    "drivetrain",
    "passenger_capacity",
    "passenger_doors",
    "body_style",
]

TOKEN_COUNT = len(SPEC_KEYS) + 1  # includes random suffix ID


def parse_filename(path: Path) -> Optional[CarImage]:
    """
    Parse a dataset filename into a CarImage object.

    Returns None if the filename does not match the expected schema.
    """
    stem = path.stem
    parts = stem.split("_")

    if len(parts) < TOKEN_COUNT:
        LOGGER.debug("Skipping %s: expected %s tokens, found %s", path.name, TOKEN_COUNT, len(parts))
        return None

    specs_raw = parts[: len(SPEC_KEYS)]
    random_id = parts[len(SPEC_KEYS)]

    specs: Dict[str, str] = {}
    for key, value in zip(SPEC_KEYS, specs_raw):
        specs[key] = value

    make = specs["make"]
    model = specs["model"]

    year_str = specs["year"]
    try:
        year = int(year_str)
    except ValueError:
        LOGGER.debug("Skipping %s: invalid year '%s'", path.name, year_str)
        return None

    identifier = stem  # full stem is already unique thanks to random suffix

    return CarImage(
        id=identifier,
        path=path,
        make=make,
        model=model,
        year=year,
        random_id=random_id,
        specs=specs,
    )
