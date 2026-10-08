-- Тестовые данные

INSERT INTO categories (name, description) VALUES
    ('Электроника', 'Электронные компоненты и устройства'),
    ('Канцтовары', 'Офисные канцелярские товары'),
    ('Инструменты', 'Ручной и электроинструмент');

INSERT INTO suppliers (name, contact_person, phone, email) VALUES
    ('ООО "ТехноПоставка"', 'Иванов Иван', '+7 900 111-22-33', 'sales@technosnab.example'),
    ('ИП Петров', 'Петров Пётр', '+7 900 444-55-66', 'petrov@example.com');

INSERT INTO warehouses (name, address) VALUES
    ('Главный склад', 'г. Москва, ул. Складская, д. 1'),
    ('Склад №2', 'г. Москва, ул. Резервная, д. 5');

INSERT INTO products (sku, name, category_id, unit, price, description) VALUES
    ('EL-001', 'Паяльник 60Вт', 1, 'шт', 850.00, 'Электрический паяльник'),
    ('EL-002', 'Мультиметр DT-830B', 1, 'шт', 650.00, 'Цифровой мультиметр'),
    ('OF-001', 'Бумага А4', 2, 'пачка', 320.00, '500 листов'),
    ('OF-002', 'Ручка шариковая', 2, 'шт', 25.00, 'Синяя'),
    ('TL-001', 'Отвёртка крестовая', 3, 'шт', 150.00, 'PH2');

-- Начальные остатки (M:M products <-> warehouses)
INSERT INTO stock (product_id, warehouse_id, quantity) VALUES
    (1, 1, 20), (2, 1, 15), (3, 1, 100), (4, 1, 500), (5, 1, 30),
    (1, 2, 5);

-- Пример уже проведённого документа прихода
INSERT INTO documents (doc_number, doc_type, warehouse_id, supplier_id, status, comment) VALUES
    ('IN-0001', 'IN', 1, 1, 'POSTED', 'Первичная поставка электроники');

INSERT INTO document_items (document_id, product_id, quantity, price) VALUES
    (1, 1, 20, 700.00),
    (1, 2, 15, 500.00);