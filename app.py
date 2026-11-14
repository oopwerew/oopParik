#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""LUMIÈRE — запуск веб-приложения на Flask."""
import os
import socket
from app import create_app


def find_available_port(start_port: int = 5001, max_tries: int = 20) -> int:
    """Поиск свободного порта (по умолчанию 5001, чтобы избежать конфликта с AirPlay на 5000 в macOS)."""
    for p in range(start_port, start_port + max_tries):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(("127.0.0.1", p))
                return p
            except OSError:
                continue
    return start_port


app = create_app()

if __name__ == "__main__":
    configured_port = int(os.environ.get("PORT", app.config.get("PORT", 5001)))
    port = find_available_port(configured_port)

    print("=" * 65)
    print("✨ LUMIÈRE — Парикмахерская и студия стиля (Flask Web App)")
    print(f"🚀 Веб-приложение запущено и доступно по адресу:")
    print(f"   👉 http://localhost:{port}")
    print(f"   👉 http://127.0.0.1:{port}")
    print("=" * 65)

    app.run(host="0.0.0.0", port=port, debug=True)
