#!/usr/bin/env python3

from __future__ import annotations

import os
import signal
import subprocess
import sys
import time
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
FRONTEND_DIR = ROOT_DIR / "App-Centro-De-Actividades" / "Frontend"
BACKEND_DIR = ROOT_DIR / "App-Centro-De-Actividades" / "Backend"
IS_WINDOWS = os.name == "nt"


def start_process(command: str, cwd: Path) -> subprocess.Popen:
    kwargs = {
        "cwd": str(cwd),
        "shell": True,
    }

    if IS_WINDOWS:
        kwargs["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP
    else:
        kwargs["start_new_session"] = True

    return subprocess.Popen(command, **kwargs)


def stop_process(process: subprocess.Popen) -> None:
    if process.poll() is not None:
        return

    try:
        if IS_WINDOWS:
            process.send_signal(signal.CTRL_BREAK_EVENT)
            process.wait(timeout=5)
        else:
            os.killpg(process.pid, signal.SIGTERM)
            process.wait(timeout=5)
    except (ProcessLookupError, subprocess.TimeoutExpired):
        pass

    if process.poll() is not None:
        return

    try:
        if IS_WINDOWS:
            process.terminate()
        else:
            os.killpg(process.pid, signal.SIGKILL)
    except ProcessLookupError:
        return

    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        pass


def main() -> int:
    if not FRONTEND_DIR.exists() or not BACKEND_DIR.exists():
        print("No se encontraron las carpetas esperadas de Frontend y Backend.")
        return 1

    print(f"Iniciando frontend en {FRONTEND_DIR}...")
    frontend = start_process("npm run dev", FRONTEND_DIR)

    print(f"Iniciando backend en {BACKEND_DIR}...")
    backend = start_process("poetry run flask --app app run", BACKEND_DIR)

    processes = [
        ("frontend", frontend),
        ("backend", backend),
    ]

    try:
        while True:
            for name, process in processes:
                return_code = process.poll()
                if return_code is not None:
                    print(f"{name} finalizo con codigo {return_code}. Cerrando el resto...")
                    return return_code

            time.sleep(0.5)
    except KeyboardInterrupt:
        print("\nInterrupcion detectada. Cerrando procesos...")
        return 0
    finally:
        for _, process in processes:
            stop_process(process)


if __name__ == "__main__":
    sys.exit(main())
