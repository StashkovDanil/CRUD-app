-- ============================================================
-- Складской учёт — схема БД (PostgreSQL)
--
-- Сущности (7 таблиц):
--   categories, suppliers, warehouses, products,
--   stock            — M:M products <-> warehouses (атрибут quantity)
--   documents, document_items — M:M documents <-> products (атрибуты quantity, price)
--
-- Связи 1:M:
--   categories  -> products    (у категории много товаров)
--   warehouses  -> documents   (у склада много документов)
--   suppliers   -> documents   (у поставщика много документов, необязательно)
-- ============================================================

CREATE TABLE IF NOT EXISTS categories (
    id          SERIAL PRIMARY KEY,
    name        VARCHAR(150) NOT NULL UNIQUE,
    description TEXT
);

CREATE TABLE IF NOT EXISTS suppliers (
    id             SERIAL PRIMARY KEY,
    name           VARCHAR(200) NOT NULL,
    contact_person VARCHAR(150),
    phone          VARCHAR(50),
    email          VARCHAR(150)
);

CREATE TABLE IF NOT EXISTS warehouses (
    id      SERIAL PRIMARY KEY,
    name    VARCHAR(150) NOT NULL UNIQUE,
    address VARCHAR(255)
);

-- 1:M — categories -> products
CREATE TABLE IF NOT EXISTS products (
    id          SERIAL PRIMARY KEY,
    sku         VARCHAR(50) NOT NULL UNIQUE,
    name        VARCHAR(200) NOT NULL,
    category_id INTEGER NOT NULL REFERENCES categories(id) ON DELETE RESTRICT,
    unit        VARCHAR(20) NOT NULL DEFAULT 'шт',
    price       NUMERIC(12, 2) NOT NULL DEFAULT 0 CHECK (price >= 0),
    description TEXT
);
CREATE INDEX IF NOT EXISTS idx_products_category ON products(category_id);

-- M:M — products <-> warehouses, с атрибутом quantity (остаток на складе)
CREATE TABLE IF NOT EXISTS stock (
    id           SERIAL PRIMARY KEY,
    product_id   INTEGER NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    warehouse_id INTEGER NOT NULL REFERENCES warehouses(id) ON DELETE CASCADE,
    quantity     NUMERIC(14, 3) NOT NULL DEFAULT 0 CHECK (quantity >= 0),
    updated_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (product_id, warehouse_id)
);

CREATE TYPE document_type AS ENUM ('IN', 'OUT');
CREATE TYPE document_status AS ENUM ('DRAFT', 'POSTED');

-- 1:M — warehouses -> documents, suppliers -> documents (необязательная связь)
CREATE TABLE IF NOT EXISTS documents (
    id           SERIAL PRIMARY KEY,
    doc_number   VARCHAR(50) NOT NULL UNIQUE,
    doc_type     document_type NOT NULL,
    warehouse_id INTEGER NOT NULL REFERENCES warehouses(id) ON DELETE RESTRICT,
    supplier_id  INTEGER REFERENCES suppliers(id) ON DELETE SET NULL,
    status       document_status NOT NULL DEFAULT 'DRAFT',
    created_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
    comment      TEXT
);
CREATE INDEX IF NOT EXISTS idx_documents_warehouse ON documents(warehouse_id);
CREATE INDEX IF NOT EXISTS idx_documents_supplier ON documents(supplier_id);

-- M:M — documents <-> products, с атрибутами quantity и price (позиции документа)
CREATE TABLE IF NOT EXISTS document_items (
    id          SERIAL PRIMARY KEY,
    document_id INTEGER NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    product_id  INTEGER NOT NULL REFERENCES products(id) ON DELETE RESTRICT,
    quantity    NUMERIC(14, 3) NOT NULL CHECK (quantity > 0),
    price       NUMERIC(12, 2) NOT NULL DEFAULT 0 CHECK (price >= 0),
    UNIQUE (document_id, product_id)
);
CREATE INDEX IF NOT EXISTS idx_document_items_document ON document_items(document_id);
CREATE INDEX IF NOT EXISTS idx_document_items_product ON document_items(product_id);