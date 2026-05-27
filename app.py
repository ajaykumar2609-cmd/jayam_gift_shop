"""
Jayam Gift Shop — Flask + MySQL Backend
========================================
pip install flask mysql-connector-python
"""

from flask import (
    Flask, render_template, request, jsonify,
    session, redirect, url_for
)
import mysql.connector
import os
import hashlib
import datetime
import random
import uuid
from functools import wraps

# ─────────────────────────────────────────────────
app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "jayam_secret_2024_change_me")

# ─── DB CONFIG ────────────────────────────────────
DB_CONFIG = {
    "host":     os.environ.get("DB_HOST",     "localhost"),
    "port":     int(os.environ.get("DB_PORT", 3306)),
    "user":     os.environ.get("DB_USER",     "root"),
    "password": os.environ.get("DB_PASSWORD", ""),
    "database": os.environ.get("DB_NAME",     "jayam_giftshop"),
    "charset":  "utf8mb4",
    "autocommit": True,
}


def get_db():
    """Return a fresh connection (simple per-request pattern)."""
    return mysql.connector.connect(**DB_CONFIG)


def query(sql: str, params: tuple = (), *, fetchone=False, fetchall=False,
          lastrowid=False):
    """Execute a query and optionally return results."""
    conn = get_db()
    cur  = conn.cursor(dictionary=True)
    cur.execute(sql, params)
    result = None
    if fetchone:
        result = cur.fetchone()
    elif fetchall:
        result = cur.fetchall()
    elif lastrowid:
        result = cur.lastrowid
    cur.close()
    conn.close()
    return result


# ─── HELPERS ──────────────────────────────────────

def hash_pw(pw: str) -> str:
    return hashlib.sha256(pw.encode()).hexdigest()


def get_session_id() -> str:
    if "session_id" not in session:
        session["session_id"] = str(uuid.uuid4())
    return session["session_id"]


def current_user():
    uid = session.get("user_id")
    if uid:
        return query("SELECT * FROM users WHERE id=%s", (uid,), fetchone=True)
    return None


def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("user_id"):
            return redirect(url_for("login_page"))
        return f(*args, **kwargs)
    return decorated


def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        u = current_user()
        if not u or u["role"] != "admin":
            return redirect(url_for("login_page"))
        return f(*args, **kwargs)
    return decorated


def safe_user(u: dict) -> dict:
    """Remove password before sending to client."""
    if u:
        u = dict(u)
        u.pop("password", None)
    return u


# ─── AUTH PAGES ───────────────────────────────────

@app.route("/login")
def login_page():
    return render_template("login.html")


@app.route("/register")
def register_page():
    return render_template("register.html")


@app.route("/api/auth/register", methods=["POST"])
def register():
    d = request.get_json(force=True)
    name     = d.get("name", "").strip()
    email    = d.get("email", "").strip().lower()
    password = d.get("password", "")

    if not name or not email or not password:
        return jsonify({"error": "All fields are required"}), 400

    existing = query("SELECT id FROM users WHERE email=%s", (email,), fetchone=True)
    if existing:
        return jsonify({"error": "Email already registered"}), 400

    uid = query(
        "INSERT INTO users (name, email, password, role) VALUES (%s,%s,%s,'user')",
        (name, email, hash_pw(password)), lastrowid=True
    )
    session["user_id"] = uid
    return jsonify({"success": True, "redirect": "/user"})


@app.route("/api/auth/login", methods=["POST"])
def login():
    d = request.get_json(force=True)
    email    = d.get("email", "").strip().lower()
    password = d.get("password", "")
    u = query(
        "SELECT * FROM users WHERE email=%s AND password=%s",
        (email, hash_pw(password)), fetchone=True
    )
    if not u:
        return jsonify({"error": "Invalid email or password"}), 401
    session["user_id"] = u["id"]
    redirect_url = "/admin" if u["role"] == "admin" else "/user"
    return jsonify({"success": True, "redirect": redirect_url, "role": u["role"]})


@app.route("/api/auth/logout", methods=["POST"])
def logout():
    session.clear()
    return jsonify({"success": True, "redirect": "/login"})


@app.route("/api/auth/me")
def me():
    u = current_user()
    if not u:
        return jsonify({"error": "Not logged in"}), 401
    payload = safe_user(u)
    if payload:
        # Keep legacy key for frontend compatibility.
        payload["_id"] = payload.get("id")
    return jsonify(payload)


# ─── SHOP (PUBLIC) ────────────────────────────────

@app.route("/")
def index():
    return render_template("index.html")


# ─── ADMIN ────────────────────────────────────────

@app.route("/admin")
@admin_required
def admin_dashboard():
    return render_template("admin.html")


@app.route("/api/admin/stats")
@admin_required
def admin_stats():
    total_orders   = query("SELECT COUNT(*) AS c FROM orders", fetchone=True)["c"]
    total_revenue  = query("SELECT COALESCE(SUM(total),0) AS s FROM orders", fetchone=True)["s"] or 0
    total_users    = query("SELECT COUNT(*) AS c FROM users WHERE role='user'", fetchone=True)["c"]
    total_products = query("SELECT COUNT(*) AS c FROM products", fetchone=True)["c"]

    recent_orders = query(
        "SELECT * FROM orders ORDER BY created_at DESC LIMIT 8", fetchall=True
    ) or []
    for o in recent_orders:
        o["created_at"] = str(o["created_at"])[:19]
        o["total"] = float(o["total"])

    # Monthly revenue
    rows = query(
        "SELECT DATE_FORMAT(created_at,'%%b') AS mo, SUM(total) AS rev "
        "FROM orders GROUP BY mo", fetchall=True
    ) or []
    monthly = {r["mo"]: float(r["rev"]) for r in rows}

    # Top products
    rows = query(
        "SELECT oi.name, SUM(oi.qty) AS sold "
        "FROM order_items oi GROUP BY oi.name ORDER BY sold DESC LIMIT 5",
        fetchall=True
    ) or []
    top_products = [[r["name"], int(r["sold"])] for r in rows]

    # Category breakdown
    rows = query(
        "SELECT p.category, SUM(oi.qty) AS sold "
        "FROM order_items oi "
        "JOIN products p ON p.id=oi.product_id "
        "GROUP BY p.category", fetchall=True
    ) or []
    category_sales = {r["category"]: int(r["sold"]) for r in rows}

    return jsonify({
        "total_orders":   total_orders,
        "total_revenue":  float(total_revenue),
        "total_users":    total_users,
        "total_products": total_products,
        "recent_orders":  recent_orders,
        "monthly_revenue": monthly,
        "top_products":   top_products,
        "category_sales": category_sales,
    })


@app.route("/api/admin/orders")
@admin_required
def admin_orders():
    orders = query("SELECT * FROM orders ORDER BY created_at DESC", fetchall=True) or []
    for o in orders:
        o["created_at"] = str(o["created_at"])[:19]
        o["total"] = float(o["total"])
        # Keep legacy nested fields expected by the current admin template.
        o["customer"] = {
            "first_name": (o.get("customer_name") or "").split(" ")[0],
            "last_name": " ".join((o.get("customer_name") or "").split(" ")[1:]),
            "email": o.get("customer_email", ""),
        }
        o["items"] = query(
            "SELECT * FROM order_items WHERE order_id=%s",
            (o["id"],), fetchall=True
        ) or []
    return jsonify(orders)


@app.route("/api/admin/orders/<int:order_id>/status", methods=["POST"])
@admin_required
def update_order_status(order_id):
    status = request.get_json(force=True).get("status")
    allowed = {"confirmed", "processing", "shipped", "delivered", "cancelled"}
    if status not in allowed:
        return jsonify({"error": "Invalid status"}), 400
    query("UPDATE orders SET status=%s WHERE id=%s", (status, order_id))
    return jsonify({"success": True})


@app.route("/api/admin/products")
@admin_required
def admin_products():
    rows = query("SELECT * FROM products ORDER BY id", fetchall=True) or []
    for r in rows:
        r["price"] = float(r["price"])
        if r["sale_price"] is not None:
            r["sale_price"] = float(r["sale_price"])
        r["desc"] = r.get("description", "")
        r["bg"] = r.get("bg_color", "#faf7f2")
    return jsonify(rows)


@app.route("/api/admin/products/add", methods=["POST"])
@admin_required
def admin_add_product():
    d = request.get_json(force=True)
    pid = query(
        "INSERT INTO products (name, emoji, description, price, sale_price, "
        "category, tag, bg_color, stock) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)",
        (
            d["name"], d.get("emoji", "🎁"), d["desc"],
            float(d["price"]),
            float(d["sale_price"]) if d.get("sale_price") else None,
            d["category"], d.get("tag", ""),
            d.get("bg", "#faf7f2"), int(d.get("stock", 0)),
        ), lastrowid=True
    )
    return jsonify({"success": True, "id": pid})


@app.route("/api/admin/products/<int:pid>", methods=["PUT"])
@admin_required
def admin_update_product(pid):
    d = request.get_json(force=True)
    query(
        "UPDATE products SET name=%s, price=%s, description=%s, stock=%s, "
        "tag=%s, category=%s WHERE id=%s",
        (
            d["name"], float(d["price"]), d["desc"],
            int(d.get("stock", 0)), d.get("tag", ""),
            d["category"], pid,
        )
    )
    return jsonify({"success": True})


@app.route("/api/admin/products/<int:pid>", methods=["DELETE"])
@admin_required
def admin_delete_product(pid):
    query("DELETE FROM products WHERE id=%s", (pid,))
    return jsonify({"success": True})


@app.route("/api/admin/users")
@admin_required
def admin_users():
    users = query("SELECT * FROM users", fetchall=True) or []
    result = []
    for u in users:
        u.pop("password", None)
        u["created_at"] = str(u["created_at"])[:10]
        u["order_count"] = query(
            "SELECT COUNT(*) AS c FROM orders WHERE customer_email=%s",
            (u["email"],), fetchone=True
        )["c"]
        result.append(u)
    return jsonify(result)


# ─── USER DASHBOARD ───────────────────────────────

@app.route("/user")
@login_required
def user_dashboard():
    return render_template("user.html")


@app.route("/api/user/orders")
@login_required
def user_orders():
    u = current_user()
    orders = query(
        "SELECT * FROM orders WHERE customer_email=%s ORDER BY created_at DESC",
        (u["email"],), fetchall=True
    ) or []
    for o in orders:
        o["created_at"] = str(o["created_at"])[:19]
        o["total"] = float(o["total"])
        o["items"] = query(
            "SELECT * FROM order_items WHERE order_id=%s",
            (o["id"],), fetchall=True
        ) or []
        for item in o["items"]:
            item["price"] = float(item["price"])
            item["line_total"] = float(item["line_total"])
    return jsonify(orders)


@app.route("/api/user/profile", methods=["PUT"])
@login_required
def update_profile():
    d   = request.get_json(force=True)
    uid = session["user_id"]
    if d.get("password"):
        query(
            "UPDATE users SET name=%s, email=%s, password=%s WHERE id=%s",
            (d["name"], d["email"], hash_pw(d["password"]), uid)
        )
    else:
        query(
            "UPDATE users SET name=%s, email=%s WHERE id=%s",
            (d["name"], d["email"], uid)
        )
    return jsonify({"success": True})


# ─── PRODUCTS (PUBLIC) ────────────────────────────

@app.route("/api/products")
def get_products():
    cat    = request.args.get("category", "all")
    search = request.args.get("search", "").strip()

    sql    = "SELECT * FROM products WHERE 1=1"
    params = []

    if cat != "all":
        sql    += " AND category=%s"
        params.append(cat)

    if search:
        sql    += " AND (name LIKE %s OR description LIKE %s)"
        like    = f"%{search}%"
        params += [like, like]

    rows = query(sql, tuple(params), fetchall=True) or []
    for r in rows:
        r["price"] = float(r["price"])
        if r["sale_price"] is not None:
            r["sale_price"] = float(r["sale_price"])
        # Frontend expects "desc" key (MongoDB version used "desc")
        r["desc"] = r.pop("description", "")
        r["bg"] = r.get("bg_color", "#faf7f2")
        r["_id"] = r["id"]
    return jsonify(rows)


@app.route("/api/products/<int:pid>")
def get_product(pid):
    p = query("SELECT * FROM products WHERE id=%s", (pid,), fetchone=True)
    if not p:
        return jsonify({"error": "Not found"}), 404
    p["price"] = float(p["price"])
    if p["sale_price"] is not None:
        p["sale_price"] = float(p["sale_price"])
    p["desc"] = p.pop("description", "")
    p["bg"] = p.get("bg_color", "#faf7f2")
    # Keep "_id" alias for frontend compatibility
    p["_id"] = p["id"]
    return jsonify(p)


@app.route("/api/products/related/<int:pid>")
def get_related_products(pid):
    p = query("SELECT * FROM products WHERE id=%s", (pid,), fetchone=True)
    if not p:
        return jsonify({"error": "Not found"}), 404
    related = query(
        "SELECT * FROM products WHERE category=%s AND id!=%s LIMIT 4",
        (p["category"], pid), fetchall=True
    ) or []
    if len(related) < 4:
        excl = tuple([r["id"] for r in related] + [pid])
        placeholders = ",".join(["%s"] * len(excl))
        extra = query(
            f"SELECT * FROM products WHERE id NOT IN ({placeholders}) LIMIT %s",
            excl + (4 - len(related),), fetchall=True
        ) or []
        related.extend(extra)
    for r in related:
        r["price"] = float(r["price"])
        if r["sale_price"] is not None:
            r["sale_price"] = float(r["sale_price"])
        r["desc"] = r.pop("description", "")
        r["bg"] = r.get("bg_color", "#faf7f2")
        r["_id"]  = r["id"]
    return jsonify(related)


# ─── CART ─────────────────────────────────────────

@app.route("/api/cart")
def get_cart():
    sid = get_session_id()
    items = query(
        "SELECT c.id AS cart_id, c.qty, p.* FROM carts c "
        "JOIN products p ON p.id=c.product_id WHERE c.session_id=%s",
        (sid,), fetchall=True
    ) or []
    result = []
    for item in items:
        item["price"] = float(item["price"])
        if item["sale_price"] is not None:
            item["sale_price"] = float(item["sale_price"])
        item["_id"]  = item["id"]
        item["desc"] = item.pop("description", "")
        item["bg"] = item.get("bg_color", "#faf7f2")
        result.append(item)
    return jsonify(result)


@app.route("/api/cart/add", methods=["POST"])
def add_to_cart():
    pid = request.get_json(force=True).get("product_id")
    sid = get_session_id()
    if not pid:
        return jsonify({"error": "product_id required"}), 400
    existing = query(
        "SELECT id, qty FROM carts WHERE session_id=%s AND product_id=%s",
        (sid, pid), fetchone=True
    )
    if existing:
        query("UPDATE carts SET qty=qty+1 WHERE id=%s", (existing["id"],))
    else:
        query(
            "INSERT INTO carts (session_id, product_id, qty) VALUES (%s,%s,1)",
            (sid, int(pid))
        )
    return jsonify({"success": True})


@app.route("/api/cart/update", methods=["POST"])
def update_cart():
    d   = request.get_json(force=True)
    sid = get_session_id()
    qty = int(d.get("qty", 1))
    cid = int(d.get("cart_id"))
    if qty <= 0:
        query("DELETE FROM carts WHERE id=%s AND session_id=%s", (cid, sid))
    else:
        query("UPDATE carts SET qty=%s WHERE id=%s AND session_id=%s", (qty, cid, sid))
    return jsonify({"success": True})


@app.route("/api/cart/remove", methods=["POST"])
def remove_from_cart():
    sid = get_session_id()
    cid = int(request.get_json(force=True)["cart_id"])
    query("DELETE FROM carts WHERE id=%s AND session_id=%s", (cid, sid))
    return jsonify({"success": True})


# ─── ORDERS ───────────────────────────────────────

@app.route("/api/orders", methods=["POST"])
def place_order():
    d   = request.get_json(force=True)
    sid = get_session_id()

    cart_items = query(
        "SELECT c.id AS cart_id, c.qty, p.* FROM carts c "
        "JOIN products p ON p.id=c.product_id WHERE c.session_id=%s",
        (sid,), fetchall=True
    ) or []

    if not cart_items:
        return jsonify({"error": "Cart is empty"}), 400

    customer = d.get("customer", {})
    order_items = []
    total = 0.0

    for item in cart_items:
        price = float(item["sale_price"]) if item["sale_price"] else float(item["price"])
        qty   = item["qty"]
        order_items.append({
            "product_id": item["id"],
            "name":       item["name"],
            "emoji":      item["emoji"],
            "price":      price,
            "qty":        qty,
            "line_total": price * qty,
        })
        total += price * qty
        # Decrement stock
        query(
            "UPDATE products SET stock=GREATEST(stock-%s,0) WHERE id=%s",
            (qty, item["id"])
        )

    order_number = "JAYA-" + str(random.randint(10000, 99999))
    first  = customer.get("first_name", "")
    last   = customer.get("last_name",  "")
    fullname = (first + " " + last).strip() or "Guest"

    order_id = query(
        "INSERT INTO orders (order_number, customer_name, customer_email, "
        "address, city, zip, gift_message, payment_method, total, status) "
        "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,'confirmed')",
        (
            order_number, fullname, customer.get("email", ""),
            customer.get("address", ""), customer.get("city", ""),
            customer.get("zip", ""), customer.get("gift_message", ""),
            customer.get("payment", "card"), round(total, 2),
        ), lastrowid=True
    )

    for oi in order_items:
        query(
            "INSERT INTO order_items "
            "(order_id, product_id, name, emoji, price, qty, line_total) "
            "VALUES (%s,%s,%s,%s,%s,%s,%s)",
            (order_id, oi["product_id"], oi["name"], oi["emoji"],
             oi["price"], oi["qty"], oi["line_total"])
        )

    # Clear cart
    query("DELETE FROM carts WHERE session_id=%s", (sid,))

    return jsonify({"success": True, "order_number": order_number, "total": round(total, 2)})


# ─── ENTRY POINT ─────────────────────────────────

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
