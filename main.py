#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Точка входа для запуска веб-приложения LUMIÈRE (Flask)."""
import os
from app import app

if __name__ == "__main__":
    port = int(os.environ.get("PORT", app.config["CONFIG"].app_port))
    print("=" * 65)
    print("✨ LUMIÈRE — Парикмахерская и студия стиля (Flask Web App)")
    print(f"🚀 Веб-приложение запущено на: http://localhost:{port}")
    print("=" * 65)
    app.run(host="127.0.0.1", port=port, debug=True)
