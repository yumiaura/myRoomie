#!/usr/bin/env python3
"""Run myRoomie without installing anything.

    python3 main.py            # start the server AND launch the Godot client
    python3 main.py server     # server only (http://127.0.0.1:8000)
    python3 main.py client     # launch the Godot client only

The server needs only the Python deps (fastapi, uvicorn, pydantic) — no
`pip install` of myRoomie itself; this script puts `server/` on the path.
The client needs the Godot 4 editor/runtime on your PATH (or set the GODOT
environment variable to its location).
"""
from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import time
import urllib.request

ROOT = os.path.dirname(os.path.abspath(__file__))
SERVER_DIR = os.path.join(ROOT, "server")
CLIENT_DIR = os.path.join(ROOT, "client")

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8800  # 8000 is a common default; pick a quieter one by default


def run_server(host: str, port: int, db: str) -> None:
    """Start the FastAPI server in this process, source-only (no install)."""
    if SERVER_DIR not in sys.path:
        sys.path.insert(0, SERVER_DIR)
    import uvicorn
    from myroomie.app import create_app

    print(f"myRoomie server → http://{host}:{port}  (db: {db})")
    uvicorn.run(create_app(db), host=host, port=port)


def find_godot() -> str | None:
    override = os.environ.get("GODOT") or os.environ.get("GODOT4")
    if override and (os.path.isfile(override) or shutil.which(override)):
        return override
    for name in ("godot4", "godot", "Godot", "godot-4", "godot.exe"):
        found = shutil.which(name)
        if found:
            return found
    return None


def launch_client(server_url: str) -> subprocess.Popen | None:
    godot = find_godot()
    if godot is None:
        print(
            "\nGodot 4 was not found on your PATH.\n"
            "Install it from https://godotengine.org/ (or set the GODOT env var),\n"
            f"then open this folder in the editor to play:\n  {CLIENT_DIR}\n"
        )
        return None
    # Everything after `--` is passed to the game as user args (see Api.gd).
    return subprocess.Popen([godot, "--path", CLIENT_DIR, "--", "--server", server_url])


def wait_for_server(host: str, port: int, timeout: float = 20.0) -> bool:
    url = f"http://{host}:{port}/health"
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=1) as response:
                if response.status == 200:
                    return True
        except OSError:
            time.sleep(0.3)
    return False


def run_both(host: str, port: int, db: str) -> None:
    server = subprocess.Popen(
        [sys.executable, os.path.abspath(__file__), "server",
         "--host", host, "--port", str(port), "--db", db]
    )
    try:
        if not wait_for_server(host, port):
            print("warning: the server did not respond in time; launching anyway.")
        client = launch_client(f"http://{host}:{port}")
        if client is None:
            print(f"Server is running at http://{host}:{port}. Press Ctrl+C to stop.")
            server.wait()
        else:
            client.wait()
    except KeyboardInterrupt:
        pass
    finally:
        server.terminate()
        try:
            server.wait(timeout=5)
        except subprocess.TimeoutExpired:
            server.kill()


def main() -> None:
    parser = argparse.ArgumentParser(description="Launch the myRoomie server and/or client.")
    parser.add_argument("mode", nargs="?", default="both", choices=["both", "server", "client"])
    parser.add_argument("--host", default=DEFAULT_HOST)
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    parser.add_argument("--db", default=os.path.join(ROOT, "myroomie.db"), help="SQLite database path")
    args = parser.parse_args()

    if args.mode == "server":
        run_server(args.host, args.port, args.db)
    elif args.mode == "client":
        client = launch_client(f"http://{args.host}:{args.port}")
        if client is None:
            sys.exit(1)
        client.wait()
    else:
        run_both(args.host, args.port, args.db)


if __name__ == "__main__":
    main()
