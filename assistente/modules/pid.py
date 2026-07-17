import json
import re
import os
import signal

from modules.config import *


def load_state():
    default = {"attivo": False, "pid2": 0, "note_pids": []}
    if not STATE_FILE.exists():
        return default
    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return default


def save_state(state):
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)

    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2, ensure_ascii=False)


def scrivistatus():
    global attivo

    # === Salva il PID del processo nel JSON ===
    state = load_state()
    state["attivo"] = attivo
    save_state(state)



def estraipid():

    try:
        with open(STATE_FILE, "r") as file:
            state = json.load(file)

        pid2 = state.get("pid2")

        if pid2:
            return int(pid2)

    except Exception as e:
        print("Errore lettura PID:", e)

    return None
