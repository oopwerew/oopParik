#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""LUMIÈRE — запуск веб-приложения на Flask."""
import os
from app import create_app

app = create_app()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", app.config.get("PORT", 5000)))
    print("=" * 65)
    print("✨ LUMIÈRE — Парикмахерская и студия стиля (Flask Web App)")
    print(f"🚀 Веб-приложение запущено на: http://localhost:{port}")
    print("=" * 65)
    app.run(host="127.0.0.1", port=port, debug=True)
