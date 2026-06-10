"""FastAPI application: the roomie lives here and the Godot client talks to it."""
from __future__ import annotations

import random
import time
import uuid

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from . import __version__, config, economy
from .models import (
    BuyRequest,
    ChoreRequest,
    CreatePetRequest,
    FeedRequest,
    GiftRequest,
    PetState,
    PlayRequest,
    PreviewRequest,
    Stats,
    Wallet,
    WearRequest,
    WorkRequest,
)
from .simulation import advance, clamp, push_event
from .storage import Store
from .traits import generate_traits


def create_app(db_path: str = "myroomie.db") -> FastAPI:
    app = FastAPI(title="myRoomie", version=__version__)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )
    store = Store(db_path)

    def load_live(pet_id: str) -> PetState:
        state = store.get(pet_id)
        if state is None:
            raise HTTPException(status_code=404, detail="roomie not found")
        advance(state, time.time())
        store.save(state)
        return state

    def run_action(pet_id: str, handler) -> PetState:
        state = load_live(pet_id)
        try:
            handler(state, time.time())
        except economy.ActionError as error:
            raise HTTPException(status_code=400, detail=str(error))
        store.save(state)
        return state

    @app.get("/health")
    def health() -> dict:
        return {"status": "ok", "version": __version__}

    @app.get("/catalog")
    def catalog() -> dict:
        return {
            "foods": config.FOODS,
            "gifts": config.GIFTS,
            "activities": config.ACTIVITIES,
            "chores": config.CHORES,
            "jobs": config.JOBS,
            "shop": config.SHOP,
        }

    @app.get("/pets")
    def list_pets() -> list[dict]:
        result = []
        for pet_id in store.list_ids():
            state = store.get(pet_id)
            if state is not None:
                result.append({"id": state.id, "name": state.name, "gender": state.gender})
        return result

    @app.post("/preview")
    def preview(req: PreviewRequest) -> dict:
        """Roll a personality for a seed without creating anything. Lets the
        client show who is about to move in, and reroll until it clicks."""
        seed = req.seed if req.seed is not None else random.randint(1, 2**31 - 1)
        return {"seed": seed, "traits": generate_traits(seed)}

    @app.post("/pets", response_model=PetState)
    def create_pet(req: CreatePetRequest) -> PetState:
        if req.gender not in ("girl", "boy"):
            raise HTTPException(status_code=400, detail="gender must be 'girl' or 'boy'")
        if not req.name.strip():
            raise HTTPException(status_code=400, detail="name cannot be empty")
        seed = req.seed if req.seed is not None else random.randint(1, 2**31 - 1)
        now = time.time()
        state = PetState(
            id=uuid.uuid4().hex,
            name=req.name.strip(),
            gender=req.gender,
            seed=seed,
            traits=generate_traits(seed),
            stats=Stats(),
            wallet=Wallet(rent_due_at=now + config.RENT_PERIOD_MIN * 60.0 / config.TIME_SCALE),
            created_at=now,
            last_tick=now,
        )
        push_event(
            state, now, "welcome",
            f"Hi! I'm {state.name}. Thanks for taking me in — make yourself at home. 🏡",
        )
        store.save(state)
        return state

    @app.get("/pets/{pet_id}", response_model=PetState)
    def get_pet(pet_id: str) -> PetState:
        return load_live(pet_id)

    @app.post("/pets/{pet_id}/visit", response_model=PetState)
    def visit(pet_id: str) -> PetState:
        state = load_live(pet_id)
        state.stats.loneliness = clamp(state.stats.loneliness - 25)
        state.stats.mood = clamp(state.stats.mood + 3)
        store.save(state)
        return state

    @app.post("/pets/{pet_id}/feed", response_model=PetState)
    def feed_pet(pet_id: str, req: FeedRequest) -> PetState:
        return run_action(pet_id, lambda state, now: economy.feed(state, req.food, now))

    @app.post("/pets/{pet_id}/wash", response_model=PetState)
    def wash_pet(pet_id: str) -> PetState:
        return run_action(pet_id, economy.wash)

    @app.post("/pets/{pet_id}/play", response_model=PetState)
    def play_pet(pet_id: str, req: PlayRequest) -> PetState:
        return run_action(pet_id, lambda state, now: economy.play(state, req.activity, now))

    @app.post("/pets/{pet_id}/gift", response_model=PetState)
    def gift_pet(pet_id: str, req: GiftRequest) -> PetState:
        return run_action(pet_id, lambda state, now: economy.gift(state, req.item, now))

    @app.post("/pets/{pet_id}/chore", response_model=PetState)
    def chore_pet(pet_id: str, req: ChoreRequest) -> PetState:
        return run_action(pet_id, lambda state, now: economy.chore(state, req.task, now))

    @app.post("/pets/{pet_id}/work", response_model=PetState)
    def work_pet(pet_id: str, req: WorkRequest) -> PetState:
        return run_action(pet_id, lambda state, now: economy.work(state, req.job, now))

    @app.post("/pets/{pet_id}/pay-rent", response_model=PetState)
    def pay_rent_pet(pet_id: str) -> PetState:
        return run_action(pet_id, economy.pay_rent)

    @app.post("/pets/{pet_id}/buy", response_model=PetState)
    def buy_item(pet_id: str, req: BuyRequest) -> PetState:
        return run_action(pet_id, lambda state, now: economy.buy(state, req.item, now))

    @app.post("/pets/{pet_id}/wear", response_model=PetState)
    def wear_item(pet_id: str, req: WearRequest) -> PetState:
        return run_action(pet_id, lambda state, now: economy.wear(state, req.item, now))

    @app.post("/pets/{pet_id}/inbox/seen", response_model=PetState)
    def mark_inbox_seen(pet_id: str) -> PetState:
        state = load_live(pet_id)
        for event in state.inbox:
            event.seen = True
        store.save(state)
        return state

    return app


app = create_app()
