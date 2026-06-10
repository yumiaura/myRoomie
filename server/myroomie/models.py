"""Pydantic models describing a roomie and the request payloads."""
from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field

from . import config


class Traits(BaseModel):
    """Generated once at creation; shapes how the roomie behaves over time."""

    personality: str
    love_language: str
    hobby: str
    favorite_food: str
    tidiness: int       # high -> tidies up on their own
    thriftiness: int    # low -> impulse-buys clothes
    sociability: int    # high -> misses you faster when you are away
    metabolism: int     # high -> gets hungry quicker
    resilience: int     # high -> resists getting sick


class Stats(BaseModel):
    hunger: float = 80.0
    hygiene: float = 80.0
    energy: float = 80.0
    mood: float = 70.0
    health: float = 90.0
    loneliness: float = 0.0
    affection: float = 0.0


class Wallet(BaseModel):
    money: int = config.STARTING_MONEY
    rent_amount: int = config.RENT_AMOUNT
    rent_due_at: float = 0.0
    rent_overdue: bool = False


class Event(BaseModel):
    """A note or happening the roomie leaves in your inbox."""

    at: float
    kind: str
    text: str
    seen: bool = False


class PetState(BaseModel):
    id: str
    name: str
    gender: str          # "girl" or "boy"
    owner: Optional[str] = None
    seed: int
    traits: Traits
    stats: Stats = Field(default_factory=Stats)
    wallet: Wallet = Field(default_factory=Wallet)
    level: int = 1
    xp: int = 0
    relationship: str = config.RELATIONSHIP_STAGES[0]
    apartment_mess: float = 10.0
    wardrobe: list[str] = Field(default_factory=list)
    outfit: Optional[str] = None
    decor: list[str] = Field(default_factory=list)
    season: str = ""
    diary: list[Event] = Field(default_factory=list)
    created_at: float = 0.0
    last_tick: float = 0.0
    inbox: list[Event] = Field(default_factory=list)


# Request payloads -----------------------------------------------------
class CreatePetRequest(BaseModel):
    name: str
    gender: str
    seed: Optional[int] = None


class PreviewRequest(BaseModel):
    seed: Optional[int] = None


class FeedRequest(BaseModel):
    food: str


class PlayRequest(BaseModel):
    activity: str


class GiftRequest(BaseModel):
    item: str


class ChoreRequest(BaseModel):
    task: str


class WorkRequest(BaseModel):
    job: str


class RegisterRequest(BaseModel):
    username: str
    password: str


class LoginRequest(BaseModel):
    username: str
    password: str


class BuyRequest(BaseModel):
    item: str


class WearRequest(BaseModel):
    item: str
