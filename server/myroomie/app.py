"""FastAPI application: the roomie lives here and the Godot client talks to it."""
from __future__ import annotations

import asyncio
import random
import time
import uuid

from fastapi import Depends, FastAPI, Header, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from . import __version__, auth, config, economy
from .models import (
    BuyRequest,
    ChoreRequest,
    CreatePetRequest,
    FeedRequest,
    GiftRequest,
    LoginRequest,
    PetState,
    PlayRequest,
    PreviewRequest,
    RegisterRequest,
    Stats,
    Wallet,
    WearRequest,
    WorkRequest,
)
from .simulation import advance, clamp, current_season, push_diary, push_event
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

    def require_user(authorization: str = Header(default="")) -> str:
        token = authorization[7:] if authorization.startswith("Bearer ") else ""
        username = store.user_for_token(token) if token else None
        if username is None:
            raise HTTPException(status_code=401, detail="not authenticated")
        return username

    def load_live(pet_id: str, username: str) -> PetState:
        state = store.get(pet_id)
        if state is None:
            raise HTTPException(status_code=404, detail="roomie not found")
        if state.owner != username:
            raise HTTPException(status_code=403, detail="that's not your roomie")
        advance(state, time.time())
        store.save(state)
        return state

    def run_action(pet_id: str, username: str, handler) -> PetState:
        state = load_live(pet_id, username)
        try:
            handler(state, time.time())
        except economy.ActionError as error:
            raise HTTPException(status_code=400, detail=str(error))
        store.save(state)
        return state

    # --- Public endpoints --------------------------------------------
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

    @app.post("/preview")
    def preview(req: PreviewRequest) -> dict:
        """Roll a personality for a seed without creating anything. Lets the
        client show who is about to move in, and reroll until it clicks."""
        seed = req.seed if req.seed is not None else random.randint(1, 2**31 - 1)
        return {"seed": seed, "traits": generate_traits(seed)}

    # --- Accounts ----------------------------------------------------
    @app.post("/auth/register")
    def register(req: RegisterRequest) -> dict:
        username = req.username.strip()
        if not username or not req.password:
            raise HTTPException(status_code=400, detail="username and password required")
        salt, pw_hash = auth.hash_password(req.password)
        if not store.create_user(username, salt, pw_hash):
            raise HTTPException(status_code=409, detail="username already taken")
        return {"status": "registered", "username": username}

    @app.post("/auth/login")
    def login(req: LoginRequest) -> dict:
        username = req.username.strip()
        record = store.get_user(username)
        if record is None or not auth.verify_password(req.password, record[0], record[1]):
            raise HTTPException(status_code=401, detail="invalid credentials")
        token = auth.generate_token()
        store.save_token(token, username)
        return {"token": token, "username": username}

    # --- Roomies (require auth) --------------------------------------
    @app.get("/pets")
    def list_pets(username: str = Depends(require_user)) -> list[dict]:
        result = []
        for pet_id in store.list_ids():
            state = store.get(pet_id)
            if state is not None and state.owner == username:
                result.append({"id": state.id, "name": state.name, "gender": state.gender})
        return result

    @app.post("/pets", response_model=PetState)
    def create_pet(req: CreatePetRequest, username: str = Depends(require_user)) -> PetState:
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
            owner=username,
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
        state.season = current_season(now)
        push_diary(state, now, "milestone", "Moved in together. 🏡")
        store.save(state)
        return state

    @app.get("/pets/{pet_id}", response_model=PetState)
    def get_pet(pet_id: str, username: str = Depends(require_user)) -> PetState:
        return load_live(pet_id, username)

    @app.post("/pets/{pet_id}/visit", response_model=PetState)
    def visit(pet_id: str, username: str = Depends(require_user)) -> PetState:
        state = load_live(pet_id, username)
        state.stats.loneliness = clamp(state.stats.loneliness - 25)
        state.stats.mood = clamp(state.stats.mood + 3)
        store.save(state)
        return state

    @app.post("/pets/{pet_id}/feed", response_model=PetState)
    def feed_pet(pet_id: str, req: FeedRequest, username: str = Depends(require_user)) -> PetState:
        return run_action(pet_id, username, lambda state, now: economy.feed(state, req.food, now))

    @app.post("/pets/{pet_id}/wash", response_model=PetState)
    def wash_pet(pet_id: str, username: str = Depends(require_user)) -> PetState:
        return run_action(pet_id, username, economy.wash)

    @app.post("/pets/{pet_id}/play", response_model=PetState)
    def play_pet(pet_id: str, req: PlayRequest, username: str = Depends(require_user)) -> PetState:
        return run_action(pet_id, username, lambda state, now: economy.play(state, req.activity, now))

    @app.post("/pets/{pet_id}/gift", response_model=PetState)
    def gift_pet(pet_id: str, req: GiftRequest, username: str = Depends(require_user)) -> PetState:
        return run_action(pet_id, username, lambda state, now: economy.gift(state, req.item, now))

    @app.post("/pets/{pet_id}/chore", response_model=PetState)
    def chore_pet(pet_id: str, req: ChoreRequest, username: str = Depends(require_user)) -> PetState:
        return run_action(pet_id, username, lambda state, now: economy.chore(state, req.task, now))

    @app.post("/pets/{pet_id}/work", response_model=PetState)
    def work_pet(pet_id: str, req: WorkRequest, username: str = Depends(require_user)) -> PetState:
        return run_action(pet_id, username, lambda state, now: economy.work(state, req.job, now))

    @app.post("/pets/{pet_id}/pay-rent", response_model=PetState)
    def pay_rent_pet(pet_id: str, username: str = Depends(require_user)) -> PetState:
        return run_action(pet_id, username, economy.pay_rent)

    @app.post("/pets/{pet_id}/buy", response_model=PetState)
    def buy_item(pet_id: str, req: BuyRequest, username: str = Depends(require_user)) -> PetState:
        return run_action(pet_id, username, lambda state, now: economy.buy(state, req.item, now))

    @app.post("/pets/{pet_id}/wear", response_model=PetState)
    def wear_item(pet_id: str, req: WearRequest, username: str = Depends(require_user)) -> PetState:
        return run_action(pet_id, username, lambda state, now: economy.wear(state, req.item, now))

    @app.post("/pets/{pet_id}/inbox/seen", response_model=PetState)
    def mark_inbox_seen(pet_id: str, username: str = Depends(require_user)) -> PetState:
        state = load_live(pet_id, username)
        for event in state.inbox:
            event.seen = True
        store.save(state)
        return state

    @app.websocket("/pets/{pet_id}/ws")
    async def pet_stream(websocket: WebSocket, pet_id: str, token: str = "") -> None:
        """Live state stream. Auth rides in the query string (`?token=`)
        because WebSocket clients can't easily set headers. Pushes a fresh,
        time-advanced snapshot every WS_PUSH_SECONDS until the client leaves."""
        username = store.user_for_token(token) if token else None
        if username is None:
            await websocket.close(code=4401)
            return
        owner_state = store.get(pet_id)
        if owner_state is None or owner_state.owner != username:
            await websocket.close(code=4404)
            return
        await websocket.accept()
        try:
            while True:
                live = store.get(pet_id)
                if live is None:
                    break
                advance(live, time.time())
                store.save(live)
                await websocket.send_text(live.model_dump_json())
                await asyncio.sleep(config.WS_PUSH_SECONDS)
        except WebSocketDisconnect:
            return

    return app


app = create_app()
