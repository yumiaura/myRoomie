"""Tunable constants and content tables for the myRoomie world.

Rates are written per in-world minute. The simulation converts them to the
real elapsed wall-clock time using TIME_SCALE, so everything in one place
stays easy to balance.
"""
from __future__ import annotations

# Time -----------------------------------------------------------------
# One real second equals TIME_SCALE in-world seconds. Raise it to make the
# roomie live faster (handy for demos and tests).
TIME_SCALE = 1.0

# Offline catch-up: a long absence is replayed in chunks of this many in-world
# minutes so several autonomous events can happen instead of just one. Beyond
# CATCHUP_MAX_CHUNKS the remainder is applied as plain drift (no event spam).
CATCHUP_CHUNK_MIN = 60.0
CATCHUP_MAX_CHUNKS = 480

# How often a live WebSocket connection pushes fresh state (real seconds).
WS_PUSH_SECONDS = 3.0

# Baseline per-minute stat drift, before personality modifiers ----------
HUNGER_DECAY_PER_MIN = 0.7
HYGIENE_DECAY_PER_MIN = 0.5
ENERGY_REGEN_PER_MIN = 0.6
LONELINESS_RISE_PER_MIN = 0.45
HEALTH_REGEN_PER_MIN = 0.25
HEALTH_DECAY_PER_MIN = 0.7
MESS_RISE_PER_MIN = 0.3

CRITICAL_LOW = 20.0
COMFORTABLE = 60.0

# Economy --------------------------------------------------------------
STARTING_MONEY = 60
RENT_AMOUNT = 120
RENT_PERIOD_MIN = 1440  # one in-world day
RENT_OVERDUE_MOOD_PENALTY = 16
RENT_OVERDUE_AFFECTION_PENALTY = 6

# Foods: name -> (hunger_restore, money_cost, joy)
FOODS = {
    "instant_noodles": (22, 4, 2),
    "home_cooked": (38, 12, 6),
    "sushi": (30, 22, 9),
    "pancakes": (28, 9, 7),
    "salad": (18, 8, 4),
    "cake": (16, 14, 11),
}

# Gifts: name -> (money_cost, joy, affection)
GIFTS = {
    "flowers": (15, 10, 7),
    "plushie": (25, 14, 10),
    "book": (18, 8, 9),
    "jewelry": (60, 18, 16),
    "concert_tickets": (80, 22, 20),
    "handwritten_letter": (0, 12, 14),
}

# Play activities: name -> (joy, affection, energy_cost, xp)
ACTIVITIES = {
    "video_games": (16, 5, 14, 12),
    "walk_in_park": (14, 8, 12, 10),
    "movie_night": (18, 10, 8, 8),
    "board_game": (15, 9, 10, 11),
    "dance": (20, 7, 20, 14),
}

# Household chores you help with: name -> (mess_cleared, energy_cost, affection, xp)
CHORES = {
    "dishes": (20, 8, 2, 6),
    "laundry": (18, 10, 2, 6),
    "vacuum": (24, 12, 3, 8),
    "groceries": (16, 9, 3, 7),
}

# Jobs that earn money: name -> (payout, energy_cost, xp, min_energy)
JOBS = {
    "freelance_art": (45, 25, 16, 25),
    "barista_shift": (35, 20, 12, 20),
    "tutoring": (50, 22, 18, 22),
    "delivery": (30, 28, 10, 28),
}

# Which activity / gift resonates with which trait --------------------
HOBBY_ACTIVITY = {
    "gaming": "video_games",
    "running": "dance",
    "guitar": "movie_night",
    "painting": "board_game",
    "gardening": "walk_in_park",
    "astronomy": "walk_in_park",
    "baking": "movie_night",
    "photography": "walk_in_park",
}

LOVE_LANGUAGE_GIFT = {
    "gifts": {"jewelry", "plushie", "flowers", "concert_tickets"},
    "words": {"handwritten_letter", "book"},
    "quality_time": {"concert_tickets", "book"},
    "acts_of_service": {"flowers", "handwritten_letter"},
}

# Shop: clothing is worn (shows as the current outfit); decor is placed and
# tidies the apartment a little. name -> {cost, kind, joy, mess_clear?}
SHOP = {
    "cozy_sweater": {"cost": 30, "kind": "clothing", "joy": 10},
    "summer_dress": {"cost": 45, "kind": "clothing", "joy": 14},
    "denim_jacket": {"cost": 40, "kind": "clothing", "joy": 12},
    "pajamas": {"cost": 20, "kind": "clothing", "joy": 8},
    "houseplant": {"cost": 25, "kind": "decor", "joy": 6, "mess_clear": 10},
    "string_lights": {"cost": 35, "kind": "decor", "joy": 10, "mess_clear": 5},
    "bookshelf": {"cost": 50, "kind": "decor", "joy": 8, "mess_clear": 15},
    "rug": {"cost": 30, "kind": "decor", "joy": 7, "mess_clear": 8},
}

# Trait vocabularies ---------------------------------------------------
PERSONALITIES = ["Sunny", "Shy", "Sassy", "Caring", "Dreamy", "Mischievous", "Calm", "Fiery"]
LOVE_LANGUAGES = ["gifts", "quality_time", "words", "acts_of_service"]
HOBBIES = ["painting", "guitar", "baking", "gaming", "gardening", "astronomy", "running", "photography"]
FAVORITE_FOODS = list(FOODS.keys())

# Relationship ladder --------------------------------------------------
RELATIONSHIP_STAGES = [
    "new_acquaintance",
    "getting_to_know",
    "friends",
    "close",
    "sweethearts",
    "inseparable",
]


def xp_to_next(level: int) -> int:
    """Experience needed to advance from the given level to the next one."""
    return 80 + level * 40
