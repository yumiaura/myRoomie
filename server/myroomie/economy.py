"""Player-driven actions: feeding, washing, playing, gifting, chores, work, rent.

Each function mutates the roomie in place and raises ActionError on anything
the player isn't allowed to do (too tired, too broke). The web layer turns
those into clean 400 responses.
"""
from __future__ import annotations

from . import config
from .models import PetState
from .simulation import clamp, push_diary, push_event, refresh_mood


class ActionError(Exception):
    """Raised when an action cannot be performed (e.g. not enough money)."""


def register_presence(state: PetState) -> None:
    """Any hands-on interaction reassures the roomie a little."""
    state.stats.loneliness = clamp(state.stats.loneliness - 6)


def grant_xp(state: PetState, amount: int) -> None:
    state.xp += amount
    while state.xp >= config.xp_to_next(state.level):
        state.xp -= config.xp_to_next(state.level)
        state.level += 1
        push_diary(state, state.last_tick, "milestone", f"Reached level {state.level}.")


def relationship_index(state: PetState) -> int:
    return config.RELATIONSHIP_STAGES.index(state.relationship)


def add_affection(state: PetState, amount: float, now: float) -> None:
    state.stats.affection += amount
    while state.stats.affection >= 100.0 and relationship_index(state) < len(config.RELATIONSHIP_STAGES) - 1:
        state.stats.affection -= 100.0
        state.relationship = config.RELATIONSHIP_STAGES[relationship_index(state) + 1]
        push_event(
            state, now, "relationship",
            f"Something shifted between you two. You're {state.relationship.replace('_', ' ')} now. 💞",
        )
        push_diary(state, now, "milestone", f"Became {state.relationship.replace('_', ' ')}.")
        for line in config.NARRATIVE_BEATS.get(state.relationship, []):
            push_event(state, now, "story", line)
        push_diary(state, now, "story", f"A new chapter: {state.relationship.replace('_', ' ')}.")
    state.stats.affection = clamp(state.stats.affection)


def feed(state: PetState, food: str, now: float) -> PetState:
    if food not in config.FOODS:
        raise ActionError(f"unknown food: {food}")
    restore, cost, joy = config.FOODS[food]
    if state.wallet.money < cost:
        raise ActionError("not enough money to buy that")
    state.wallet.money -= cost
    state.stats.hunger = clamp(state.stats.hunger + restore)
    favourite = food == state.traits.favorite_food
    state.stats.mood = clamp(state.stats.mood + joy * 0.4 + (6 if favourite else 0))
    if favourite:
        push_event(state, now, "happy", f"Their favourite — {food.replace('_', ' ')}! {state.name} beams. 😍")
    register_presence(state)
    grant_xp(state, 3)
    refresh_mood(state)
    return state


def wash(state: PetState, now: float) -> PetState:
    if state.stats.energy < 5:
        raise ActionError("too tired to freshen up")
    state.stats.hygiene = clamp(state.stats.hygiene + 42)
    state.stats.energy = clamp(state.stats.energy - 6)
    state.stats.mood = clamp(state.stats.mood + 4)
    register_presence(state)
    grant_xp(state, 3)
    refresh_mood(state)
    return state


def play(state: PetState, activity: str, now: float) -> PetState:
    if activity not in config.ACTIVITIES:
        raise ActionError(f"unknown activity: {activity}")
    joy, affection, energy_cost, xp = config.ACTIVITIES[activity]
    if state.stats.energy < energy_cost:
        raise ActionError("too tired to play right now")
    state.stats.energy = clamp(state.stats.energy - energy_cost)
    state.stats.hunger = clamp(state.stats.hunger - 5)
    state.stats.mood = clamp(state.stats.mood + joy)
    state.stats.loneliness = clamp(state.stats.loneliness - 30)
    bonus = 5 if config.HOBBY_ACTIVITY.get(state.traits.hobby) == activity else 0
    add_affection(state, affection + bonus, now)
    grant_xp(state, xp)
    refresh_mood(state)
    return state


def gift(state: PetState, item: str, now: float) -> PetState:
    if item not in config.GIFTS:
        raise ActionError(f"unknown gift: {item}")
    cost, joy, affection = config.GIFTS[item]
    if state.wallet.money < cost:
        raise ActionError("not enough money for that gift")
    state.wallet.money -= cost
    resonates = item in config.LOVE_LANGUAGE_GIFT.get(state.traits.love_language, set())
    multiplier = 1.6 if resonates else 1.0
    state.stats.mood = clamp(state.stats.mood + joy)
    add_affection(state, affection * multiplier, now)
    register_presence(state)
    if resonates:
        push_event(state, now, "happy", f"\"You really get me.\" {state.name} hugs the {item.replace('_', ' ')}. 🥰")
    grant_xp(state, 4)
    refresh_mood(state)
    return state


def chore(state: PetState, task: str, now: float) -> PetState:
    if task not in config.CHORES:
        raise ActionError(f"unknown chore: {task}")
    cleared, energy_cost, affection, xp = config.CHORES[task]
    if state.stats.energy < energy_cost:
        raise ActionError("not enough energy for chores")
    state.stats.energy = clamp(state.stats.energy - energy_cost)
    state.apartment_mess = clamp(state.apartment_mess - cleared)
    state.stats.mood = clamp(state.stats.mood + 3)
    add_affection(state, affection, now)
    register_presence(state)
    grant_xp(state, xp)
    refresh_mood(state)
    return state


def work(state: PetState, job: str, now: float) -> PetState:
    if job not in config.JOBS:
        raise ActionError(f"unknown job: {job}")
    payout, energy_cost, xp, min_energy = config.JOBS[job]
    if state.stats.energy < min_energy:
        raise ActionError("not enough energy to take that shift")
    state.stats.energy = clamp(state.stats.energy - energy_cost)
    state.wallet.money += payout
    state.stats.mood = clamp(state.stats.mood - 3)
    register_presence(state)
    grant_xp(state, xp)
    refresh_mood(state)
    return state


def buy(state: PetState, item: str, now: float) -> PetState:
    if item not in config.SHOP:
        raise ActionError(f"unknown item: {item}")
    spec = config.SHOP[item]
    if state.wallet.money < spec["cost"]:
        raise ActionError("not enough money to buy that")
    if spec["kind"] == "clothing":
        if item in state.wardrobe:
            raise ActionError("they already own that outfit")
        state.wallet.money -= spec["cost"]
        state.wardrobe.append(item)
        state.outfit = item
    else:  # decor
        if item in state.decor:
            raise ActionError("that's already in the apartment")
        state.wallet.money -= spec["cost"]
        state.decor.append(item)
        state.apartment_mess = clamp(state.apartment_mess - spec.get("mess_clear", 0))
    state.stats.mood = clamp(state.stats.mood + spec.get("joy", 0))
    add_affection(state, 2, now)
    register_presence(state)
    grant_xp(state, 4)
    refresh_mood(state)
    return state


def wear(state: PetState, item: str, now: float) -> PetState:
    if item not in state.wardrobe:
        raise ActionError("they don't own that yet")
    state.outfit = item
    state.stats.mood = clamp(state.stats.mood + 3)
    refresh_mood(state)
    return state


def pay_rent(state: PetState, now: float) -> PetState:
    wallet = state.wallet
    if wallet.money < wallet.rent_amount:
        raise ActionError("not enough money for rent")
    wallet.money -= wallet.rent_amount
    wallet.rent_overdue = False
    wallet.rent_due_at = now + config.RENT_PERIOD_MIN * 60.0 / config.TIME_SCALE
    state.stats.mood = clamp(state.stats.mood + 8)
    add_affection(state, 4, now)
    push_event(state, now, "rent", "Rent paid. A weight off both your shoulders. 🏠")
    refresh_mood(state)
    return state
