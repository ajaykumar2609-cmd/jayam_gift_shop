-- ══════════════════════════════════════════════════
--  JAYAM GIFT SHOP — MySQL Schema
-- ══════════════════════════════════════════════════

CREATE DATABASE IF NOT EXISTS jayam_giftshop
    DEFAULT CHARACTER SET utf8mb4
    DEFAULT COLLATE utf8mb4_unicode_ci;

USE jayam_giftshop;

-- ── Users ──────────────────────────────────────────
CREATE TABLE IF NOT EXISTS users (
    id         INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    name       VARCHAR(120)  NOT NULL,
    email      VARCHAR(255)  NOT NULL UNIQUE,
    password   CHAR(64)      NOT NULL,          -- SHA-256 hex
    role       ENUM('user','admin') NOT NULL DEFAULT 'user',
    created_at TIMESTAMP     NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- ── Products ───────────────────────────────────────
CREATE TABLE IF NOT EXISTS products (
    id         INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    name       VARCHAR(200)   NOT NULL,
    emoji      VARCHAR(10)    NOT NULL DEFAULT '🎁',
    description TEXT           NOT NULL,
    price      DECIMAL(10,2)  NOT NULL,
    sale_price DECIMAL(10,2)  NULL,
    category   ENUM('wellness','home','food','accessories','stationery') NOT NULL DEFAULT 'wellness',
    tag        ENUM('popular','new','sale','') NOT NULL DEFAULT '',
    bg_color   VARCHAR(20)    NOT NULL DEFAULT '#faf7f2',
    stock      INT UNSIGNED   NOT NULL DEFAULT 0,
    created_at TIMESTAMP      NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- ── Sessions / Carts ──────────────────────────────
CREATE TABLE IF NOT EXISTS carts (
    id         INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    session_id VARCHAR(36)   NOT NULL,
    product_id INT UNSIGNED  NOT NULL,
    qty        INT UNSIGNED  NOT NULL DEFAULT 1,
    UNIQUE KEY uq_session_product (session_id, product_id),
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- ── Orders ────────────────────────────────────────
CREATE TABLE IF NOT EXISTS orders (
    id             INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    order_number   VARCHAR(20)   NOT NULL UNIQUE,
    customer_name  VARCHAR(200)  NOT NULL,
    customer_email VARCHAR(255)  NOT NULL,
    address        TEXT          NULL,
    city           VARCHAR(100)  NULL,
    zip            VARCHAR(20)   NULL,
    gift_message   TEXT          NULL,
    payment_method VARCHAR(30)   NOT NULL DEFAULT 'card',
    total          DECIMAL(10,2) NOT NULL,
    status         ENUM('confirmed','processing','shipped','delivered','cancelled') NOT NULL DEFAULT 'confirmed',
    created_at     TIMESTAMP     NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- ── Order Items ───────────────────────────────────
CREATE TABLE IF NOT EXISTS order_items (
    id         INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    order_id   INT UNSIGNED  NOT NULL,
    product_id INT UNSIGNED  NOT NULL,
    name       VARCHAR(200)  NOT NULL,
    emoji      VARCHAR(10)   NOT NULL,
    price      DECIMAL(10,2) NOT NULL,
    qty        INT UNSIGNED  NOT NULL,
    line_total DECIMAL(10,2) NOT NULL,
    FOREIGN KEY (order_id)   REFERENCES orders(id)   ON DELETE CASCADE,
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE RESTRICT
) ENGINE=InnoDB;

-- ══════════════════════════════════════════════════
--  SEED DATA
-- ══════════════════════════════════════════════════

-- Default users  (password = SHA-256 of plaintext)
--   admin@jaya.com / admin123
--   alice@example.com / alice123
--   bob@example.com   / bob123
INSERT IGNORE INTO users (name, email, password, role) VALUES
('Admin',  'admin@jaya.com',      '240be518fabd2724ddb6f04eeb1da5967448d7e831c08c8fa822809f74c720a9', 'admin'),
('Alice',  'alice@example.com',   '723a0d17ecafd5b95d3d2e0fb7e80c3e4e9d1d62e2494a6f40e1d6d66e5db5a6', 'user'),
('Bob',    'bob@example.com',     '8d059c3640b97180dd2ee453e20d34ab0cb0f2eccbe87d01915a8e578a202b11', 'user');

-- Products
INSERT IGNORE INTO products (name, emoji, description, price, sale_price, category, tag, bg_color, stock) VALUES
('Botanical Candle',     '🕯️', 'Hand-poured soy wax with lavender & bergamot. Burns for 50+ hours.',              28.00, NULL,  'wellness',    'popular', '#fef3e2', 42),
('Linen Throw',          '🧣',  'Stonewashed French linen in dusty sage. Lightweight and luxurious.',              64.00, NULL,  'home',        'new',     '#edf4ef', 18),
('Artisan Tea Set',      '🍵',  'Six hand-blended teas in a keepsake box with a cast-iron infuser.',               42.00, NULL,  'food',        'popular', '#fdf1e8', 35),
('Leather Journal',      '📔',  'Full-grain vegetable-tanned leather. 240 pages of thick ivory paper.',            38.00, NULL,  'stationery',  '',        '#f0ebe3', 27),
('Pressed Flower Print', '🌸',  'Original botanical illustration, archival giclée print on 300gsm.',               52.00, NULL,  'home',        'new',     '#fce8f1', 12),
('Bath Ritual Kit',      '🛁',  'Dead Sea salts, rose oil, and a wooden bath tray. Pure indulgence.',              56.00, NULL,  'wellness',    'popular', '#e8f0fe', 20),
('Spiced Chocolate Box', '🍫',  'Twelve single-origin dark chocolates with unexpected spice pairings.',            22.00, 18.00,'food',        'sale',    '#fdf1e8', 55),
('Silk Eye Mask',        '😴',  '22 momme mulberry silk, adjustable strap. Sleep like royalty.',                   34.00, NULL,  'accessories', 'new',     '#ede0f5', 30),
('Wildflower Honey',     '🍯',  'Raw, unfiltered honey from alpine meadows. A jar of pure sunshine.',              18.00, NULL,  'food',        '',        '#fef3cc', 60),
('Ceramic Mug Set',      '☕',  'Set of two hand-thrown mugs in a warm speckled glaze.',                           46.00, NULL,  'home',        'popular', '#f5ede0', 22),
('Gratitude Cards',      '💌',  '50 beautifully illustrated prompt cards to deepen connections.',                  16.00, NULL,  'stationery',  '',        '#fff0f0', 80),
('Gold Ear Cuff Set',    '✨',  'Three mismatched 14k gold-plated cuffs. No piercing required.',                   44.00, 34.00,'accessories', 'sale',    '#fdf8e1', 16);
