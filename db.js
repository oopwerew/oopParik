// ============================================================
//  Слой доступа к БД. Каждая таблица = отдельный класс-репозиторий.
// ============================================================
const mysql = require('mysql2/promise');

class Database {
    constructor(config) {
        this.pool = mysql.createPool({
            host: config.host,
            port: config.port,
            user: config.user,
            password: config.password,
            database: config.database,
            charset: 'utf8mb4',
            decimalNumbers: true,      // DECIMAL приходит числом, а не строкой
            dateStrings: true,         // DATE приходит строкой 'YYYY-MM-DD'
            waitForConnections: true,
            connectionLimit: 10
        });
    }

    async query(sql, params = []) {
        const [rows] = await this.pool.execute(sql, params);
        return rows;
    }

    async ping() {
        await this.query('SELECT 1');
    }
}

class UserRepository {
    constructor(db) { this.db = db; }

    async findByLogin(login) {
        const rows = await this.db.query('SELECT * FROM users WHERE login = ?', [login]);
        return rows[0] || null;
    }

    async create({ fullName, phone, login, passwordHash }) {
        const res = await this.db.query(
            'INSERT INTO users (full_name, phone, login, password_hash) VALUES (?, ?, ?, ?)',
            [fullName, phone, login, passwordHash]
        );
        return res.insertId;
    }

    async updateHash(id, passwordHash) {
        await this.db.query('UPDATE users SET password_hash = ? WHERE id = ?', [passwordHash, id]);
    }
}

class ServiceRepository {
    constructor(db) { this.db = db; }

    static SELECT = `
        SELECT s.id, s.title, c.name AS category, s.price, s.duration,
               s.description AS \`desc\`, s.emoji, s.image_url AS image
        FROM services s
        JOIN categories c ON c.id = s.category_id`;

    async findAll() {
        return this.db.query(`${ServiceRepository.SELECT} ORDER BY s.id DESC`);
    }

    async findById(id) {
        const rows = await this.db.query(`${ServiceRepository.SELECT} WHERE s.id = ?`, [id]);
        return rows[0] || null;
    }

    async create({ title, category, price, duration, desc, emoji, image }) {
        const cat = await this.db.query('SELECT id FROM categories WHERE name = ?', [category]);
        if (!cat.length) throw new Error('Неизвестная категория: ' + category);
        const res = await this.db.query(
            `INSERT INTO services (category_id, title, price, duration, description, emoji, image_url)
             VALUES (?, ?, ?, ?, ?, ?, ?)`,
            [cat[0].id, title, price, duration || null, desc || null, emoji || null, image || null]
        );
        return this.findById(res.insertId);
    }

    async remove(id) {
        const res = await this.db.query('DELETE FROM services WHERE id = ?', [id]);
        return res.affectedRows > 0;
    }
}

class BookingRepository {
    constructor(db) { this.db = db; }

    static SELECT = `
        SELECT id, user_id AS userId, service_id AS serviceId, service_title AS serviceTitle,
               price, client_name AS clientName, client_phone AS clientPhone,
               master_name AS master, booking_date AS date, booking_time AS time
        FROM bookings`;

    async findByUser(userId) {
        return this.db.query(`${BookingRepository.SELECT} WHERE user_id = ? ORDER BY id DESC`, [userId]);
    }

    async findById(id) {
        const rows = await this.db.query(`${BookingRepository.SELECT} WHERE id = ?`, [id]);
        return rows[0] || null;
    }

    async create(b) {
        const res = await this.db.query(
            `INSERT INTO bookings (user_id, service_id, service_title, price, client_name,
                                   client_phone, master_name, booking_date, booking_time)
             VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)`,
            [b.userId, b.serviceId, b.serviceTitle, b.price, b.clientName,
             b.clientPhone, b.master, b.date, b.time]
        );
        return this.findById(res.insertId);
    }

    async remove(id) {
        const res = await this.db.query('DELETE FROM bookings WHERE id = ?', [id]);
        return res.affectedRows > 0;
    }
}

module.exports = { Database, UserRepository, ServiceRepository, BookingRepository };
