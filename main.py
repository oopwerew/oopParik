#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Точка входа для запуска веб-приложения LUMIÈRE (Flask)."""
import os
import subprocess
from app import create_app

PORT = 5001


def ensure_port_free(port: int):
    try:
        out = subprocess.check_output(["lsof", "-t", f"-i:{port}"], stderr=subprocess.DEVNULL).decode().strip()
        if out:
            current_pid = str(os.getpid())
            for pid in out.split():
                if pid != current_pid:
                    try:
                        os.kill(int(pid), 9)
                    except OSError:
                        pass
    except Exception:
        pass


app = create_app()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", app.config.get("PORT", PORT)))

    if os.environ.get("WERKZEUG_RUN_MAIN") != "true":
        ensure_port_free(port)
        print("=" * 65)
        print("✨ LUMIÈRE — Парикмахерская и студия стиля (Flask Web App)")
        print(f"🚀 Веб-приложение запущено и доступно по адресу:")
        print(f"   👉 http://localhost:{port}")
        print("=" * 65)

    app.run(host="localhost", port=port, debug=True)
