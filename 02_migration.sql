-- Дополнение к основной схеме: поля для карточек на сайте (эмодзи и фото).
-- Выполнить ОДИН раз в MySQL Workbench после основного скрипта.
USE lumiere_salon;

ALTER TABLE services
    ADD COLUMN emoji VARCHAR(16) NULL AFTER description,
    ADD COLUMN image_url VARCHAR(500) NULL AFTER emoji;

UPDATE services SET emoji = '✂️'   WHERE id = 1;
UPDATE services SET emoji = '💈'   WHERE id = 2;
UPDATE services SET emoji = '🌸'   WHERE id = 3;
UPDATE services SET emoji = '🎨'   WHERE id = 4;
UPDATE services SET emoji = '✨'   WHERE id = 5;
UPDATE services SET emoji = '🌿'   WHERE id = 6;
UPDATE services SET emoji = '💫'   WHERE id = 7;
UPDATE services SET emoji = '🧖‍♀️' WHERE id = 8;
UPDATE services SET emoji = '👁️'  WHERE id = 9;
UPDATE services SET emoji = '🧴'   WHERE id = 10;
