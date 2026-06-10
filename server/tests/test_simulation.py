import random

from myroomie import config
from myroomie.models import PetState, Stats, Wallet
from myroomie.simulation import advance
from myroomie.traits import generate_traits


def make_pet(seed: int = 42, now: float = 1_000_000.0) -> PetState:
    return PetState(
        id="test",
        name="Mira",
        gender="girl",
        seed=seed,
        traits=generate_traits(seed),
        stats=Stats(),
        wallet=Wallet(rent_due_at=now + config.RENT_PERIOD_MIN * 60),
        created_at=now,
        last_tick=now,
    )


def test_hunger_and_loneliness_drift_over_time():
    now = 1_000_000.0
    pet = make_pet(now=now)
    start_hunger = pet.stats.hunger
    advance(pet, now + 3600, rng=random.Random(0))  # one hour later
    assert pet.stats.hunger < start_hunger
    assert pet.stats.loneliness > 0
    assert pet.last_tick == now + 3600


def test_no_change_when_no_time_passes():
    now = 1_000_000.0
    pet = make_pet(now=now)
    snapshot = pet.model_copy(deep=True)
    advance(pet, now, rng=random.Random(0))
    assert pet.stats.hunger == snapshot.stats.hunger
    assert pet.stats.loneliness == snapshot.stats.loneliness


def test_rent_becomes_overdue_after_due_date():
    now = 1_000_000.0
    pet = make_pet(now=now)
    advance(pet, now + config.RENT_PERIOD_MIN * 60 + 10, rng=random.Random(0))
    assert pet.wallet.rent_overdue is True
    assert any(event.kind == "rent" for event in pet.inbox)


def test_neglect_eventually_harms_health():
    now = 1_000_000.0
    pet = make_pet(now=now)
    pet.stats.hunger = 5.0
    pet.stats.hygiene = 5.0
    advance(pet, now + 3600 * 6, rng=random.Random(0))
    assert pet.stats.health < 90.0
