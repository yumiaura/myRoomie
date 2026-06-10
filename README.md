<h1 align="center">myRoomie</h1>

<p align="center"><em>You signed the lease. Someone moved in. They've been waiting for you to come home.</em></p>

<p align="center">
  <img alt="status" src="https://img.shields.io/badge/status-early%20MVP-ff9aa2">
  <img alt="client" src="https://img.shields.io/badge/client-Godot%204-478cbf">
  <img alt="server" src="https://img.shields.io/badge/server-FastAPI-009688">
  <img alt="python" src="https://img.shields.io/badge/python-3.10%2B-3776ab">
  <img alt="license" src="https://img.shields.io/badge/license-MIT-blue">
</p>

---

**myRoomie** is a tiny 2D life-sim about sharing a small apartment with someone who is genuinely their own person. Pick who moves in — a girl or a boy — and a personality is rolled just for them: how tidy they are, how easily they get lonely, what they love, how recklessly they spend. No two roomies are quite alike.

The catch: they keep living whether you're watching or not. Their day runs on a real clock on the server, so when you come back after a while, you come back to *something* — a place that's been lived in, a mood that drifted, a note left on the counter.

## What you actually do

- 🍳 **Look after them** — feed, freshen up, and keep the place from falling apart.
- 🎮 **Spend time together** — play, take walks, have movie nights. It's how you grow close.
- 🎁 **Surprise them** — gifts land differently depending on who they are. Some people just want a handwritten note.
- 🧹 **Split the chores** — pitch in around the apartment so it stays a home.
- 💼 **Make rent** — pick up shifts that cost energy, earn coins, and keep a roof over both your heads.
- 📈 **Watch a relationship grow** — experience, levels, and a bond that deepens the more you show up.

## The part that gets you

Your roomie has a life of their own when you're gone. They might blow a little money on an outfit they couldn't resist. They might tidy up to surprise you. They might leave you a note just because they were thinking of you — or because the apartment got too quiet and they started to miss you. Stay away too long and it shows: the mood dips, the sulking starts, and they can even get sick.

Come home often. They notice.

## Quickstart

**No install** — from the repo root (needs `fastapi`, `uvicorn`, `pydantic`, and Godot 4 on your PATH):

```bash
python3 main.py            # starts the server and launches the client
# python3 main.py server   # server only, on http://127.0.0.1:8800
# python3 main.py client   # client only
```

**Or install the server** (Python 3.10+):

```bash
pip install -e .
myroomie                 # serves on http://127.0.0.1:8800
```

Then open the `client/` folder in Godot 4.2+ and press ▶. Create your roomie and move in.

### Build a desktop app

Export the client to a standalone binary:

```bash
python3 main.py export --platform linux     # → client/build/myRoomie.x86_64
python3 main.py export --platform windows    # → client/build/myRoomie.exe
python3 main.py export --platform mac        # → client/build/myRoomie.app
```

This needs the Godot 4 editor (on your PATH or via the `GODOT` env var) plus the
matching **export templates** installed (Editor → Manage Export Templates). Use
`--out DIR` to change the output directory.

## Under the hood

A **Godot 4** client talks to a **FastAPI** server over plain HTTP. The server owns the simulation — it ages every roomie forward to *now* on each request, so the world keeps turning even with the client closed. State lives in SQLite; personalities are generated from a seed, so they're reproducible.

## Status

Early but real: you can create a roomie, live the full feed / wash / play / gift / chore / work / rent loop, and get notes back. Art is placeholder for now — the file names are the contract, so dropping in real portraits is a no-code change.

⭐ **Star the repo** to follow along — the apartment's only going to get more lived-in from here.

---

<sub>MIT licensed. Built with Godot and FastAPI.</sub>
