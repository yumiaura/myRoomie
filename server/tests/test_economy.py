import pytest

from myroomie import economy
from myroomie.models import PetState, Stats, Wallet
from myroomie.traits import generate_traits

NOW = 1_000_000.0


def make_pet(seed: int = 7) -> PetState:
    return PetState(
        id="test",
        name="Kai",
        gender="boy",
        seed=seed,
        traits=generate_traits(seed),
        stats=Stats(),
        wallet=Wallet(money=100, rent_amount=120, rent_due_at=NOW + 10_000),
        created_at=NOW,
        last_tick=NOW,
    )


def test_feed_restores_hunger_and_costs_money():
    pet = make_pet()
    pet.stats.hunger = 40.0
    money_before = pet.wallet.money
    economy.feed(pet, "home_cooked", NOW)
    assert pet.stats.hunger > 40.0
    assert pet.wallet.money < money_before


def test_feed_unknown_food_raises():
    pet = make_pet()
    with pytest.raises(economy.ActionError):
        economy.feed(pet, "moon_rocks", NOW)


def test_work_earns_money_but_needs_energy():
    pet = make_pet()
    pet.stats.energy = 90.0
    money_before = pet.wallet.money
    economy.work(pet, "tutoring", NOW)
    assert pet.wallet.money > money_before
    pet.stats.energy = 1.0
    with pytest.raises(economy.ActionError):
        economy.work(pet, "tutoring", NOW)


def test_pay_rent_clears_overdue_and_reschedules():
    pet = make_pet()
    pet.wallet.money = 200
    pet.wallet.rent_overdue = True
    economy.pay_rent(pet, NOW)
    assert pet.wallet.rent_overdue is False
    assert pet.wallet.rent_due_at > NOW
    assert pet.wallet.money == 80


def test_pay_rent_blocked_when_broke():
    pet = make_pet()
    pet.wallet.money = 10
    with pytest.raises(economy.ActionError):
        economy.pay_rent(pet, NOW)


def test_play_builds_affection_and_relationship():
    pet = make_pet()
    pet.stats.energy = 100.0
    pet.stats.affection = 98.0
    economy.play(pet, "movie_night", NOW)
    assert pet.relationship == "getting_to_know"


def test_promotion_delivers_story_beats():
    pet = make_pet()
    pet.stats.energy = 100.0
    pet.stats.affection = 98.0
    economy.play(pet, "movie_night", NOW)
    assert pet.relationship == "getting_to_know"
    assert any(entry.kind == "story" for entry in pet.inbox)
    assert any(entry.kind == "story" for entry in pet.diary)


def test_gift_grants_affection():
    pet = make_pet()
    affection_before = pet.stats.affection
    economy.gift(pet, "flowers", NOW)
    assert pet.stats.affection > affection_before


def test_buy_clothing_adds_to_wardrobe_and_wears_it():
    pet = make_pet()
    pet.wallet.money = 100
    economy.buy(pet, "cozy_sweater", NOW)
    assert "cozy_sweater" in pet.wardrobe
    assert pet.outfit == "cozy_sweater"
    assert pet.wallet.money == 70


def test_buy_duplicate_clothing_raises():
    pet = make_pet()
    pet.wallet.money = 100
    economy.buy(pet, "cozy_sweater", NOW)
    with pytest.raises(economy.ActionError):
        economy.buy(pet, "cozy_sweater", NOW)


def test_buy_decor_clears_mess():
    pet = make_pet()
    pet.wallet.money = 100
    pet.apartment_mess = 50.0
    economy.buy(pet, "bookshelf", NOW)
    assert "bookshelf" in pet.decor
    assert pet.apartment_mess < 50.0


def test_wear_unowned_raises():
    pet = make_pet()
    with pytest.raises(economy.ActionError):
        economy.wear(pet, "summer_dress", NOW)


def test_leveling_up_from_xp():
    pet = make_pet()
    pet.stats.energy = 100.0
    level_before = pet.level
    for round_index in range(20):
        pet.stats.energy = 100.0
        economy.play(pet, "dance", NOW)
    assert pet.level > level_before
    assert any("level" in entry.text.lower() for entry in pet.diary)
