-- ============================================================
--  LUMIÈRE — полный скрипт БД (MySQL 8.0, Workbench)
--  Соответствует модели «Бд_Парикден.mwb» + поля emoji и image_url
--  для карточек на сайте. Запускать ОДИН файл целиком (молния ⚡).
--  Внимание: скрипт пересоздаёт базу — все старые данные удаляются.
-- ============================================================
DROP DATABASE IF EXISTS lumiere_salon;
CREATE DATABASE lumiere_salon
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_0900_ai_ci;
USE lumiere_salon;

-- 1. Клиенты (регистрация и вход с сайта)
CREATE TABLE users (
    id            INT          NOT NULL AUTO_INCREMENT,
    full_name     VARCHAR(100) NOT NULL,
    phone         VARCHAR(30)  NOT NULL,
    login         VARCHAR(100) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at    DATETIME     NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    UNIQUE INDEX login_UNIQUE (login ASC) VISIBLE
) ENGINE = InnoDB;

-- 2. Категории услуг
CREATE TABLE categories (
    id   INT         NOT NULL AUTO_INCREMENT,
    name VARCHAR(80) NOT NULL,
    PRIMARY KEY (id),
    UNIQUE INDEX name_UNIQUE (name ASC) VISIBLE
) ENGINE = InnoDB;

-- 3. Услуги и товары
CREATE TABLE services (
    id          INT           NOT NULL AUTO_INCREMENT,
    category_id INT           NOT NULL,
    title       VARCHAR(150)  NOT NULL,
    price       DECIMAL(10,2) NOT NULL,
    duration    VARCHAR(50)   NULL DEFAULT NULL,
    description TEXT          NULL DEFAULT NULL,
    emoji       VARCHAR(16)   NULL DEFAULT NULL,
    image_url   VARCHAR(500)  NULL DEFAULT NULL,
    PRIMARY KEY (id),
    INDEX fk_services_categories_idx (category_id ASC) VISIBLE,
    CONSTRAINT fk_services_categories
        FOREIGN KEY (category_id) REFERENCES categories (id)
        ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE = InnoDB;

-- 4. Онлайн-записи клиентов
CREATE TABLE bookings (
    id            INT           NOT NULL AUTO_INCREMENT,
    user_id       INT           NULL DEFAULT NULL,
    service_id    INT           NOT NULL,
    service_title VARCHAR(150)  NOT NULL,
    price         DECIMAL(10,2) NOT NULL,
    client_name   VARCHAR(100)  NOT NULL,
    client_phone  VARCHAR(30)   NOT NULL,
    master_name   VARCHAR(100)  NOT NULL,
    booking_date  DATE          NOT NULL,
    booking_time  VARCHAR(20)   NOT NULL,
    created_at    DATETIME      NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    INDEX fk_bookings_users_idx (user_id ASC) VISIBLE,
    INDEX fk_bookings_services_idx (service_id ASC) VISIBLE,
    CONSTRAINT fk_bookings_users
        FOREIGN KEY (user_id) REFERENCES users (id)
        ON DELETE SET NULL ON UPDATE CASCADE,
    CONSTRAINT fk_bookings_services
        FOREIGN KEY (service_id) REFERENCES services (id)
        ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE = InnoDB;

-- ------------------------------------------------------------
--  Начальные данные
-- ------------------------------------------------------------
INSERT INTO categories (id, name) VALUES
(1, 'Стрижки'),
(2, 'Окрашивание'),
(3, 'Укладки и уход'),
(4, 'Доп. услуги'),
(5, 'Товары для дома');

INSERT INTO services (id, category_id, title, price, duration, description, emoji) VALUES
(1,  1, 'Женская модельная стрижка + укладка',        2800.00, '60 мин',  'Мытьё головы с массажем, подбор формы и лёгкая укладка феном', '✂️'),
(2,  1, 'Мужская стрижка (Классика / Fade)',          1900.00, '45 мин',  'Точная работа ножницами и машинкой, окантовка и укладка',       '💈'),
(3,  4, 'Стрижка чёлки и коррекция кончиков',          900.00, '25 мин',  'Обновление формы чёлки и ровный срез кончиков',                 '🌸'),
(4,  2, 'Окрашивание в один тон (Корни + длина)',     4800.00, '120 мин', 'Бережное безаммиачное окрашивание с глубоким блеском',          '🎨'),
(5,  2, 'Сложное окрашивание AirTouch / Балаяж',      8900.00, '180 мин', 'Создание плавного рельефного блонда с уходом',                  '✨'),
(6,  3, 'Кератиновое восстановление и ботокс волос',  5200.00, '110 мин', 'Глубокое питание и зеркальный глянец',                          '🌿'),
(7,  3, 'Вечерняя укладка / Голливудские локоны',     2600.00, '60 мин',  'Стойкие воздушные локоны или элегантный пучок',                 '💫'),
(8,  4, 'Пилинг кожи головы + ампульный SPA-массаж',  2100.00, '40 мин',  'Детокс-очищение кожи головы и витаминная сыворотка',            '🧖‍♀️'),
(9,  4, 'Оформление и окрашивание бровей',            1400.00, '35 мин',  'Подбор архитектуры бровей и стойкое окрашивание',               '👁️'),
(10, 5, 'Увлажняющая маска с маслом арганы',          2300.00, '250 мл',  'Профессиональная салонная маска для домашнего ухода',           '🧴');

-- Тестовый клиент (пароль 123456; при первом входе сервер сам заменит его на хэш)
INSERT INTO users (full_name, phone, login, password_hash) VALUES
('Алина Ветрова', '+7 (999) 123-45-67', 'alina_style', '123456');

-- Проверка
SELECT s.id, c.name AS category, s.title, s.price, s.emoji
FROM services s JOIN categories c ON c.id = s.category_id
ORDER BY s.id;
