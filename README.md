# 🎁 Jayam Gift Shop — Full Stack

## Pages & Roles
| URL       | Who can access | Description               |
|-----------|----------------|---------------------------|
| /         | Everyone       | Animated gift shop        |
| /login    | Everyone       | Sign in page              |
| /register | Everyone       | Create account            |
| /user     | Logged-in user | User dashboard            |
| /admin    | Admin only     | Admin dashboard           |

## Demo Credentials
| Role  | Email                 | Password  |
|-------|-----------------------|-----------|
| Admin | admin@jaya.com     | admin123  |
| User  | alice@example.com     | alice123  |
| User  | bob@example.com       | bob123    |

## Tech Stack
| Layer    | Technology        |
|----------|-------------------|
| Backend  | Python + Flask    |
| Database | MongoDB           |
| Frontend | HTML + CSS + JS   |
| Auth     | Session + SHA-256 |

## Features

### Shop
- Animated splash screen, hero canvas, custom cursor
- Product grid with filters + search
- Cart panel, product modal, checkout, order success

### Admin Dashboard (/admin)
- Stats: Revenue, Orders, Users, Products
- Revenue bar chart + Category donut chart
- Recent orders table
- Full order management (status updates)
- Product CRUD (add, edit, delete)
- User management table
- Responsive sidebar navigation

### User Dashboard (/user)
- Overview: total orders, spent, wishlist count
- Order history with status tracking
- Wishlist with add-to-cart
- Profile editor (name, email, password)
- Quick actions panel

## Quick Start
```bash
# 1. Start MongoDB
mongod

# 2. Install
pip install -r requirements.txt

# 3. Run
python app.py

# 4. Open
http://localhost:5000
```

## Project Structure
```
giftshop/
├── app.py                 # Flask + MongoDB + Auth
├── requirements.txt
├── templates/
│   ├── index.html         # Animated shop
│   ├── login.html         # Sign in page
│   ├── register.html      # Register page
│   ├── admin.html         # Admin dashboard
│   └── user.html          # User dashboard
└── static/
    ├── css/style.css      # Shop styles + animations
    ├── js/app.js          # Shop JavaScript
    ├── manifest.json      # PWA manifest
    ├── sw.js              # Service worker
    └── icons/             # App icons
```
