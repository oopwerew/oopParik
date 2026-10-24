# LUMIÈRE — мост «сайт ↔ MySQL»

## Запуск (один раз)
1. В MySQL Workbench выполните ваш скрипт `gemini-code-...sql`, затем `db/02_migration.sql`.
2. Установите Node.js (https://nodejs.org, версия LTS).
3. В папке проекта: скопируйте `.env.example` → `.env`, впишите пароль от MySQL.
4. В терминале в этой папке:
       npm install
       npm start
5. Откройте http://localhost:3000 (именно так, а не двойным кликом по html).

## API
POST /api/auth/register   — регистрация (таблица users)
POST /api/auth/login      — вход
GET/POST /api/services, DELETE /api/services/:id
GET /api/bookings?userId=, POST /api/bookings, DELETE /api/bookings/:id
