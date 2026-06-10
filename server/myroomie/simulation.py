"""The living clock of a roomie.

`advance` fast-forwards a roomie from its last recorded tick to *now*. It is
called on every read and every action, so the roomie keeps living whether or
not the client is open. That is what makes them miss you, get bored, and
quietly chip away at the rent while you are gone.
"""
from __future__ import annotations

import random

from . import config
from .models import Event, PetState

INBOX_LIMIT = 50


def clamp(value: float, low: float = 0.0, high: float = 100.0) -> float:
    return max(low, min(high, value))


def clamp_prob(value: float) -> float:
    return max(0.0, min(0.9, value))


def push_event(state: PetState, now: float, kind: str, text: str) -> None:
    state.inbox.append(Event(at=now, kind=kind, text=text))
    if len(state.inbox) > INBOX_LIMIT:
        del state.inbox[: len(state.inbox) - INBOX_LIMIT]


def advance(state: PetState, now: float, rng: random.Random | None = None) -> PetState:
    """Move the roomie's whole world forward to `now`."""
    if rng is None:
        rng = random.Random(int(now) ^ state.seed)
    elapsed = max(0.0, now - state.last_tick)
    if elapsed <= 0.0:
        return state
    minutes = (elapsed * config.TIME_SCALE) / 60.0

    # Replay the absence in chunks so a long time away produces a believable
    # trail of events, not a single one.
    remaining = minutes
    chunks = 0
    while remaining > 0.0 and chunks < config.CATCHUP_MAX_CHUNKS:
        step = min(config.CATCHUP_CHUNK_MIN, remaining)
        apply_drift(state, step)
        spawn_autonomous_events(state, step, now, rng)
        remaining -= step
        chunks += 1
    if remaining > 0.0:
        # Absence longer than we simulate event-by-event: apply the rest as
        # plain drift so stats stay accurate without flooding the inbox.
        apply_drift(state, remaining)

    update_rent(state, now)
    refresh_mood(state)
    state.last_tick = now
    return state


def apply_drift(state: PetState, minutes: float) -> None:
    traits = state.traits
    stats = state.stats

    metabolism = 0.6 + traits.metabolism / 100.0   # 0.6 .. 1.6
    sociability = 0.5 + traits.sociability / 100.0

    stats.hunger = clamp(stats.hunger - config.HUNGER_DECAY_PER_MIN * metabolism * minutes)
    stats.hygiene = clamp(stats.hygiene - config.HYGIENE_DECAY_PER_MIN * minutes)

    mess_rate = config.MESS_RISE_PER_MIN * (1.2 - traits.tidiness / 100.0)
    state.apartment_mess = clamp(state.apartment_mess + mess_rate * minutes)

    regen = config.ENERGY_REGEN_PER_MIN * (0.4 if stats.hunger < config.CRITICAL_LOW else 1.0)
    stats.energy = clamp(stats.energy + regen * minutes)

    stats.loneliness = clamp(stats.loneliness + config.LONELINESS_RISE_PER_MIN * sociability * minutes)

    if stats.hunger < config.CRITICAL_LOW or stats.hygiene < config.CRITICAL_LOW:
        fragility = 1.6 - traits.resilience / 100.0
        stats.health = clamp(stats.health - config.HEALTH_DECAY_PER_MIN * fragility * minutes)
    elif stats.hunger > config.COMFORTABLE and stats.hygiene > config.COMFORTABLE and stats.loneliness < 50:
        stats.health = clamp(stats.health + config.HEALTH_REGEN_PER_MIN * minutes)


def update_rent(state: PetState, now: float) -> None:
    wallet = state.wallet
    if wallet.rent_due_at and now >= wallet.rent_due_at and not wallet.rent_overdue:
        wallet.rent_overdue = True
        state.stats.affection = clamp(state.stats.affection - config.RENT_OVERDUE_AFFECTION_PENALTY)
        push_event(state, now, "rent", "Rent is due — a note from the landlord slipped under the door. 💸")


def refresh_mood(state: PetState) -> None:
    stats = state.stats
    mood = (
        stats.hunger * 0.25
        + stats.hygiene * 0.20
        + stats.health * 0.20
        + (100.0 - stats.loneliness) * 0.20
        + (100.0 - state.apartment_mess) * 0.15
    )
    if state.wallet.rent_overdue:
        mood -= config.RENT_OVERDUE_MOOD_PENALTY
    stats.mood = clamp(mood)


def spawn_autonomous_events(state: PetState, minutes: float, now: float, rng: random.Random) -> None:
    """The roomie does their own thing: shops, sulks, tidies, leaves notes."""
    hours = minutes / 60.0
    if hours <= 0.0:
        return
    traits = state.traits

    # Impulse shopping — more likely for a low-thriftiness roomie.
    shop_chance = clamp_prob((1.1 - traits.thriftiness / 100.0) * 0.25 * hours)
    if state.wallet.money > 25 and rng.random() < shop_chance:
        bought = autonomous_buy(state, rng)
        if bought is not None:
            push_event(
                state, now, "shopping",
                f"{state.name} came home with a new {bought.replace('_', ' ')}. \"Do I look cute? 🛍️\"",
            )
        else:
            spent = rng.randint(10, min(40, state.wallet.money))
            state.wallet.money -= spent
            state.stats.mood = clamp(state.stats.mood + 6)
            push_event(
                state, now, "shopping",
                f"{state.name} treated themselves to a little something (-{spent} coins). 🛍️",
            )

    # Missing you when the loneliness builds up.
    if state.stats.loneliness > 55 and rng.random() < clamp_prob(0.4 * hours):
        push_event(state, now, "lonely", lonely_note(state, rng))

    # A sweet, unprompted note once they are attached to you.
    if state.stats.affection > 30 and rng.random() < clamp_prob(0.2 * hours):
        push_event(state, now, "note", sweet_note(state, rng))

    # A tidy roomie cleans up on their own.
    if state.apartment_mess > 50 and traits.tidiness > 60 and rng.random() < clamp_prob(0.5 * hours):
        state.apartment_mess = clamp(state.apartment_mess - 25)
        push_event(state, now, "chore", f"{state.name} tidied the place while you were out. It sparkles. ✨")

    # Getting sick when health bottoms out.
    if state.stats.health < 30 and rng.random() < clamp_prob(0.3 * hours):
        push_event(state, now, "sick", f"{state.name} isn't feeling well and curled up under a blanket. 🤒")


def autonomous_buy(state: PetState, rng: random.Random) -> str | None:
    """The roomie buys a clothing item they don't own yet and puts it on.
    Returns the item name, or None if they own everything affordable."""
    options = [
        name
        for name, spec in config.SHOP.items()
        if spec["kind"] == "clothing"
        and name not in state.wardrobe
        and spec["cost"] <= state.wallet.money
    ]
    if not options:
        return None
    choice = rng.choice(options)
    spec = config.SHOP[choice]
    state.wallet.money -= spec["cost"]
    state.wardrobe.append(choice)
    state.outfit = choice
    state.stats.mood = clamp(state.stats.mood + spec.get("joy", 0))
    return choice


LONELY_LINES = [
    "It's quiet here without you. When are you coming back?",
    "I keep glancing at the door. Hope you didn't forget about me.",
    "I saved you the window seat. It's lonelier than I'd like to admit.",
    "Talked to the houseplant today. It's a poor substitute for you.",
]

SWEET_LINES = [
    "Left you tea by the kettle, still warm if you hurry. ☕",
    "Doodled you on a sticky note. Don't laugh at my handwriting.",
    "Thinking of you. That's the whole message.",
    "Made it through the day knowing you'd be back. 💛",
]


def lonely_note(state: PetState, rng: random.Random) -> str:
    return rng.choice(LONELY_LINES)


def sweet_note(state: PetState, rng: random.Random) -> str:
    return rng.choice(SWEET_LINES)
