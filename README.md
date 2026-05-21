# Jayam Gift Shop — Flask + MySQL

A full-stack gift shop web application converted from MongoDB to MySQL.

## Stack
| Layer     | Technology                  |
|-----------|-----------------------------|
| Backend   | Python 3.10+ / Flask 3      |
| Database  | MySQL 8+                    |
| Frontend  | Plain HTML + CSS + Vanilla JS |
| Templates | Jinja2                      |

---

## Quick Start

### 1. Create the database & tables

```bash
mysql -u root -p < schema.sql
```

This creates the `jayam_giftshop` database, all tables, and seeds demo data.

**Demo accounts:**
| Email               | Password  | Role  |
|---------------------|-----------|-------|
| admin@jaya.com      | admin123  | Admin |
| alice@example.com   | alice123  | User  |
| bob@example.com     | bob123    | User  |

### 2. Install Python dependencies

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Configure environment

```bash
cp .env.example .env
# Edit .env with your MySQL credentials
```

The app reads these environment variables (falls back to defaults for local dev):

| Variable     | Default      | Description               |
|--------------|--------------|---------------------------|
| SECRET_KEY   | (hardcoded)  | Flask session secret      |
| DB_HOST      | localhost    | MySQL host                |
| DB_PORT      | 3306         | MySQL port                |
| DB_USER      | root         | MySQL user                |
| DB_PASSWORD  | (empty)      | MySQL password            |
| DB_NAME      | jayam_giftshop | Database name           |

### 4. Run

```bash
python app.py
```

Open http://localhost:5000

---

## Project Structure

```
giftshop/
├── app.py              ← Flask routes + MySQL logic
├── schema.sql          ← Database DDL + seed data
├── requirements.txt
├── .env.example
├── templates/
│   ├── index.html      ← Public shop
│   ├── login.html
│   ├── register.html
│   ├── user.html       ← User dashboard
│   └── admin.html      ← Admin dashboard
└── static/
    ├── css/style.css
    ├── js/app.js
    └── icons/
```

---

## API Endpoints

### Auth
| Method | Path                   | Description          |
|--------|------------------------|----------------------|
| GET    | /login                 | Login page           |
| GET    | /register              | Register page        |
| POST   | /api/auth/login        | Login (JSON)         |
| POST   | /api/auth/register     | Register (JSON)      |
| POST   | /api/auth/logout       | Logout               |
| GET    | /api/auth/me           | Current user info    |

### Products (public)
| Method | Path                           | Description             |
|--------|--------------------------------|-------------------------|
| GET    | /api/products                  | List (filter/search)    |
| GET    | /api/products/<id>             | Single product          |
| GET    | /api/products/related/<id>     | Related products        |

### Cart (session-based)
| Method | Path              | Description       |
|--------|-------------------|-------------------|
| GET    | /api/cart         | Get cart          |
| POST   | /api/cart/add     | Add item          |
| POST   | /api/cart/update  | Update qty        |
| POST   | /api/cart/remove  | Remove item       |

### Orders
| Method | Path         | Description   |
|--------|--------------|---------------|
| POST   | /api/orders  | Place order   |

### Admin (login required, role=admin)
| Method | Path                                   | Description          |
|--------|----------------------------------------|----------------------|
| GET    | /api/admin/stats                       | Dashboard stats      |
| GET    | /api/admin/orders                      | All orders           |
| POST   | /api/admin/orders/<id>/status          | Update status        |
| GET    | /api/admin/products                    | All products         |
| POST   | /api/admin/products/add                | Add product          |
| PUT    | /api/admin/products/<id>               | Update product       |
| DELETE | /api/admin/products/<id>               | Delete product       |
| GET    | /api/admin/users                       | All users            |

### User (login required)
| Method | Path               | Description       |
|--------|--------------------|-------------------|
| GET    | /api/user/orders   | My orders         |
| PUT    | /api/user/profile  | Update profile    |

---

## Key Changes from MongoDB Version

1. **Database** — Switched from MongoDB/pymongo to MySQL/mysql-connector-python.
2. **IDs** — MongoDB `ObjectId` strings replaced with MySQL auto-increment integers. The API still returns an `_id` alias for frontend compatibility.
3. **Schema** — Embedded documents (cart items, order items) converted to proper relational tables with foreign keys.
4. **Passwords** — SHA-256 hashing retained (upgrade to bcrypt for production).
5. **No seed function** — Initial data is in `schema.sql` via `INSERT IGNORE`.
