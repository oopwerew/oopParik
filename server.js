// ============================================================
//  LUMIÈRE — бэкенд-мост: сайт  <->  MySQL (lumiere_salon)
//  Запуск:  npm install  →  npm start  →  http://localhost:3000
// ============================================================
require('dotenv').config();
const path = require('path');
const express = require('express');
const cors = require('cors');
const bcrypt = require('bcryptjs');
const { Database, UserRepository, ServiceRepository, BookingRepository } = require('./db');

const db = new Database({
    host: process.env.DB_HOST || 'localhost',
    port: Number(process.env.DB_PORT) || 3306,
    user: process.env.DB_USER || 'root',
    password: process.env.DB_PASSWORD || '',
    database: process.env.DB_NAME || 'lumiere_salon'
});
const users = new UserRepository(db);
const services = new ServiceRepository(db);
const bookings = new BookingRepository(db);

const app = express();
app.use(cors());
app.use(express.json());
app.use(express.static(path.join(__dirname, 'public'))); // сайт отдаётся с этого же сервера

// Обёртка: ловит ошибки async-обработчиков
const wrap = (fn) => (req, res) => fn(req, res).catch((err) => {
    console.error('[ОШИБКА]', err.message);
    res.status(500).json({ ok: false, error: 'Ошибка сервера: ' + err.message });
});

// Данные пользователя, безопасные для отправки на сайт (без хэша пароля)
const publicUser = (u) => ({ id: u.id, name: u.full_name, phone: u.phone, login: u.login });

/* ---------------------------- АВТОРИЗАЦИЯ ---------------------------- */
app.post('/api/auth/register', wrap(async (req, res) => {
    const name = String(req.body.name || '').trim();
    const phone = String(req.body.phone || '').trim();
    const login = String(req.body.login || '').trim();
    const password = String(req.body.password || '');

    if (!name || !phone || !login || password.length < 4) {
        return res.status(400).json({ ok: false, error: 'Заполните все поля (пароль — минимум 4 символа)' });
    }
    if (await users.findByLogin(login)) {
        return res.status(409).json({ ok: false, error: 'Этот логин уже занят' });
    }

    const passwordHash = await bcrypt.hash(password, 10);
    const id = await users.create({ fullName: name, phone, login, passwordHash });
    res.status(201).json({ ok: true, user: { id, name, phone, login } });
}));

app.post('/api/auth/login', wrap(async (req, res) => {
    const login = String(req.body.login || '').trim();
    const password = String(req.body.password || '');
    const user = await users.findByLogin(login);

    let valid = false;
    if (user) {
        if (user.password_hash.startsWith('$2')) {
            valid = await bcrypt.compare(password, user.password_hash);
        } else {
            // Старая запись с паролем открытым текстом (тестовый клиент) —
            // проверяем и сразу заменяем на безопасный хэш
            valid = password === user.password_hash;
            if (valid) await users.updateHash(user.id, await bcrypt.hash(password, 10));
        }
    }
    if (!valid) return res.status(401).json({ ok: false, error: 'Неверный логин или пароль' });
    res.json({ ok: true, user: publicUser(user) });
}));

/* ------------------------------- УСЛУГИ ------------------------------ */
app.get('/api/services', wrap(async (req, res) => {
    res.json({ ok: true, services: await services.findAll() });
}));

app.post('/api/services', wrap(async (req, res) => {
    const { title, category, price, duration, desc, emoji, image } = req.body;
    if (!title || !category || !(Number(price) >= 0)) {
        return res.status(400).json({ ok: false, error: 'Укажите название, категорию и цену' });
    }
    try {
        const service = await services.create({ title: String(title).trim(), category, price: Number(price), duration, desc, emoji, image });
        res.status(201).json({ ok: true, service });
    } catch (err) {
        res.status(400).json({ ok: false, error: err.message });
    }
}));

app.delete('/api/services/:id', wrap(async (req, res) => {
    const removed = await services.remove(Number(req.params.id));
    res.status(removed ? 200 : 404).json({ ok: removed });
}));

/* ------------------------------- ЗАПИСИ ------------------------------ */
app.get('/api/bookings', wrap(async (req, res) => {
    const userId = Number(req.query.userId);
    if (!userId) return res.status(400).json({ ok: false, error: 'Нужен userId' });
    res.json({ ok: true, bookings: await bookings.findByUser(userId) });
}));

app.post('/api/bookings', wrap(async (req, res) => {
    const b = req.body;
    const service = await services.findById(Number(b.serviceId));
    if (!service) return res.status(404).json({ ok: false, error: 'Услуга не найдена' });
    if (!b.clientName || !b.clientPhone || !b.master || !b.date || !b.time) {
        return res.status(400).json({ ok: false, error: 'Заполните все поля записи' });
    }
    // Название и цену берём из БД, а не от клиента — их нельзя подменить
    const booking = await bookings.create({
        userId: b.userId ? Number(b.userId) : null,
        serviceId: service.id,
        serviceTitle: service.title,
        price: service.price,
        clientName: String(b.clientName).trim(),
        clientPhone: String(b.clientPhone).trim(),
        master: b.master,
        date: b.date,
        time: b.time
    });
    res.status(201).json({ ok: true, booking });
}));

app.delete('/api/bookings/:id', wrap(async (req, res) => {
    const removed = await bookings.remove(Number(req.params.id));
    res.status(removed ? 200 : 404).json({ ok: removed });
}));

/* ------------------------------- СТАРТ ------------------------------- */
const PORT = Number(process.env.PORT) || 3000;
db.ping()
    .then(() => {
        console.log('✅ Подключение к MySQL (lumiere_salon) установлено');
        app.listen(PORT, () => console.log(`🚀 Сайт и API: http://localhost:${PORT}`));
    })
    .catch((err) => {
        console.error('❌ Не удалось подключиться к MySQL:', err.message);
        console.error('   Проверьте пароль в файле .env и что MySQL запущен.');
        process.exit(1);
    });
