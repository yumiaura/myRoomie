"""Procedural generation of a roomie's personality from a numeric seed."""
from __future__ import annotations

import random

from . import config
from .models import Traits


def generate_traits(seed: int) -> Traits:
    """Build a reproducible personality. The same seed always yields the
    same roomie, which keeps creation previews and tests deterministic."""
    rng = random.Random(seed)
    return Traits(
        personality=rng.choice(config.PERSONALITIES),
        love_language=rng.choice(config.LOVE_LANGUAGES),
        hobby=rng.choice(config.HOBBIES),
        favorite_food=rng.choice(config.FAVORITE_FOODS),
        tidiness=rng.randint(15, 95),
        thriftiness=rng.randint(10, 95),
        sociability=rng.randint(20, 95),
        metabolism=rng.randint(25, 90),
        resilience=rng.randint(25, 90),
    )
