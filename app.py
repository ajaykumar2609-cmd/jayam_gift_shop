from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from pymongo import MongoClient
from bson import ObjectId
import os, datetime, random, uuid, hashlib

app = Flask(__name__)
app.secret_key = "jaya_secret_2024"

MONGO_URI    = os.environ.get("MONGO_URI", "mongodb+srv://ajaykumardeveloper12_db_user:Momdad@223@ajay.cfzt5ua.mongodb.net/?appName=ajay")
client       = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
db           = client["jaya_giftshop"]
try:
    client.admin.command('ping')
    print("✅ Connected to MongoDB")
except Exception as e:
    print(f"❌ MongoDB connection failed: {e}")
    print("Please ensure MongoDB is running locally or set MONGO_URI environment variable to a valid Atlas connection string.")

products_col = db["products"]
orders_col   = db["orders"]
cart_col     = db["carts"]
users_col    = db["users"]

# ── Helpers ────────────────────────────────────────────
def hash_pw(pw): return hashlib.sha256(pw.encode()).hexdigest()
def serialize(doc):
    if not doc:
        return doc
    doc = dict(doc)
    for key, value in list(doc.items()):
        if isinstance(value, ObjectId):
            doc[key] = str(value)
        elif isinstance(value, datetime.datetime):
            doc[key] = value.isoformat()
        elif isinstance(value, dict):
            doc[key] = serialize(value)
        elif isinstance(value, list):
            doc[key] = [serialize(item) if isinstance(item, dict) else item for item in value]
    return doc
def get_session_id():
    if "session_id" not in session:
        session["session_id"] = str(uuid.uuid4())
    return session["session_id"]
def current_user():
    uid = session.get("user_id")
    if uid:
        u = users_col.find_one({"_id": ObjectId(uid)})
        return serialize(u) if u else None
    return None
def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("user_id"):
            return redirect(url_for("login_page"))
        return f(*args, **kwargs)
    return decorated
def admin_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        u = current_user()
        if not u or u.get("role") != "admin":
            return redirect(url_for("login_page"))
        return f(*args, **kwargs)
    return decorated

# ── Seed ──────────────────────────────────────────────
def seed():
    if products_col.count_documents({}) == 0:
        products_col.insert_many([
            {"name":"Botanical Candle",    "emoji":"🕯️","desc":"Hand-poured soy wax with lavender & bergamot. Burns for 50+ hours.","price":28,"category":"wellness",   "tag":"popular","bg":"#fef3e2","stock":42},
            {"name":"Linen Throw",         "emoji":"🧣", "desc":"Stonewashed French linen in dusty sage. Lightweight and luxurious.","price":64,"category":"home",       "tag":"new",    "bg":"#edf4ef","stock":18},
            {"name":"Artisan Tea Set",     "emoji":"🍵", "desc":"Six hand-blended teas in a keepsake box with a cast-iron infuser.", "price":42,"category":"food",       "tag":"popular","bg":"#fdf1e8","stock":35},
            {"name":"Leather Journal",     "emoji":"📔", "desc":"Full-grain vegetable-tanned leather. 240 pages of thick ivory paper.","price":38,"category":"stationery","tag":"",      "bg":"#f0ebe3","stock":27},
            {"name":"Pressed Flower Print","emoji":"🌸", "desc":"Original botanical illustration, archival giclée print on 300gsm.","price":52,"category":"home",       "tag":"new",    "bg":"#fce8f1","stock":12},
            {"name":"Bath Ritual Kit",     "emoji":"🛁", "desc":"Dead Sea salts, rose oil, and a wooden bath tray. Pure indulgence.","price":56,"category":"wellness",   "tag":"popular","bg":"#e8f0fe","stock":20},
            {"name":"Spiced Chocolate Box","emoji":"🍫", "desc":"Twelve single-origin dark chocolates with unexpected spice pairings.","price":22,"category":"food",      "tag":"sale",   "bg":"#fdf1e8","stock":55,"sale_price":18},
            {"name":"Silk Eye Mask",       "emoji":"😴", "desc":"22 momme mulberry silk, adjustable strap. Sleep like royalty.",    "price":34,"category":"accessories","tag":"new",    "bg":"#ede0f5","stock":30},
            {"name":"Wildflower Honey",    "emoji":"🍯", "desc":"Raw, unfiltered honey from alpine meadows. A jar of pure sunshine.","price":18,"category":"food",      "tag":"",       "bg":"#fef3cc","stock":60},
            {"name":"Ceramic Mug Set",     "emoji":"☕", "desc":"Set of two hand-thrown mugs in a warm speckled glaze.",            "price":46,"category":"home",       "tag":"popular","bg":"#f5ede0","stock":22},
            {"name":"Gratitude Cards",     "emoji":"💌", "desc":"50 beautifully illustrated prompt cards to deepen connections.",   "price":16,"category":"stationery","tag":"",       "bg":"#fff0f0","stock":80},
            {"name":"Gold Ear Cuff Set",   "emoji":"✨", "desc":"Three mismatched 14k gold-plated cuffs. No piercing required.",    "price":44,"category":"accessories","tag":"sale",   "bg":"#fdf8e1","stock":16,"sale_price":34},
        ])
    def ensure_user(email, name, password, role):
        user = users_col.find_one({"email": email})
        if not user:
            users_col.insert_one({
                "name": name,
                "email": email,
                "password": hash_pw(password),
                "role": role,
                "created_at": datetime.datetime.utcnow(),
            })
        elif user.get("role") != role or user.get("password") != hash_pw(password):
            users_col.update_one({"_id": user["_id"]}, {"$set": {
                "name": name,
                "password": hash_pw(password),
                "role": role,
            }})

    ensure_user("admin@jaya.com", "Admin", "admin123", "admin")
    ensure_user("alice@example.com", "Alice", "alice123", "user")
    ensure_user("bob@example.com", "Bob", "bob123", "user")
    print("✅ Seeded products + users")

# ── Auth Pages ─────────────────────────────────────────
@app.route("/login")
def login_page(): return render_template("login.html")

@app.route("/register")
def register_page(): return render_template("register.html")

@app.route("/api/auth/register", methods=["POST"])
def register():
    d = request.json
    if users_col.find_one({"email": d["email"]}):
        return jsonify({"error": "Email already registered"}), 400
    uid = users_col.insert_one({
        "name": d["name"], "email": d["email"],
        "password": hash_pw(d["password"]), "role": "user",
        "created_at": datetime.datetime.utcnow()
    }).inserted_id
    session["user_id"] = str(uid)
    return jsonify({"success": True, "redirect": "/user"})

@app.route("/api/auth/login", methods=["POST"])
def login():
    d = request.json
    u = users_col.find_one({"email": d["email"], "password": hash_pw(d["password"])})
    if not u: return jsonify({"error": "Invalid email or password"}), 401
    session["user_id"] = str(u["_id"])
    redirect_url = "/admin" if u["role"] == "admin" else "/user"
    return jsonify({"success": True, "redirect": redirect_url, "role": u["role"]})

@app.route("/api/auth/logout", methods=["POST"])
def logout():
    session.clear()
    return jsonify({"success": True, "redirect": "/login"})

@app.route("/api/auth/me")
def me():
    u = current_user()
    if not u: return jsonify({"error": "Not logged in"}), 401
    u.pop("password", None)
    return jsonify(u)

# ── Shop ───────────────────────────────────────────────
@app.route("/")
def index(): return render_template("index.html")

# ── Admin Dashboard ────────────────────────────────────
@app.route("/admin")
@admin_required
def admin_dashboard(): return render_template("admin.html")

@app.route("/api/admin/stats")
@admin_required
def admin_stats():
    total_orders   = orders_col.count_documents({})
    total_revenue  = sum(o.get("total", 0) for o in orders_col.find())
    total_users    = users_col.count_documents({"role": "user"})
    total_products = products_col.count_documents({})
    recent_orders  = [serialize(o) for o in orders_col.find().sort("created_at", -1).limit(8)]
    for o in recent_orders:
        o["created_at"] = str(o.get("created_at",""))[:19]
    # Monthly revenue (last 6 months)
    monthly = {}
    for o in orders_col.find():
        dt = o.get("created_at")
        if dt:
            key = dt.strftime("%b") if hasattr(dt,"strftime") else str(dt)[:7]
            monthly[key] = monthly.get(key, 0) + o.get("total", 0)
    # Top products
    product_sales = {}
    for o in orders_col.find():
        for item in o.get("items", []):
            n = item.get("name","")
            product_sales[n] = product_sales.get(n, 0) + item.get("qty", 0)
    top_products = sorted(product_sales.items(), key=lambda x: -x[1])[:5]
    # Category breakdown
    cat_sales = {}
    for p in products_col.find():
        cat = p.get("category","other")
        sold = product_sales.get(p.get("name",""), 0)
        cat_sales[cat] = cat_sales.get(cat, 0) + sold
    return jsonify({
        "total_orders": total_orders,
        "total_revenue": round(total_revenue, 2),
        "total_users": total_users,
        "total_products": total_products,
        "recent_orders": recent_orders,
        "monthly_revenue": monthly,
        "top_products": top_products,
        "category_sales": cat_sales,
    })

@app.route("/api/admin/orders")
@admin_required
def admin_orders():
    orders = [serialize(o) for o in orders_col.find().sort("created_at",-1)]
    for o in orders: o["created_at"] = str(o.get("created_at",""))[:19]
    return jsonify(orders)

@app.route("/api/admin/orders/<order_id>/status", methods=["POST"])
@admin_required
def update_order_status(order_id):
    status = request.json.get("status")
    orders_col.update_one({"_id": ObjectId(order_id)}, {"$set": {"status": status}})
    return jsonify({"success": True})

@app.route("/api/admin/products")
@admin_required
def admin_products():
    return jsonify([serialize(p) for p in products_col.find()])

@app.route("/api/admin/products/add", methods=["POST"])
@admin_required
def admin_add_product():
    d = request.json
    pid = products_col.insert_one({
        "name": d["name"], "emoji": d.get("emoji","🎁"),
        "desc": d["desc"], "price": float(d["price"]),
        "category": d["category"], "tag": d.get("tag",""),
        "bg": d.get("bg","#faf7f2"), "stock": int(d.get("stock",0)),
    }).inserted_id
    return jsonify({"success": True, "id": str(pid)})

@app.route("/api/admin/products/<pid>", methods=["PUT"])
@admin_required
def admin_update_product(pid):
    d = request.json
    products_col.update_one({"_id": ObjectId(pid)}, {"$set": {
        "name": d["name"], "price": float(d["price"]),
        "desc": d["desc"], "stock": int(d.get("stock",0)),
        "tag": d.get("tag",""), "category": d["category"],
    }})
    return jsonify({"success": True})

@app.route("/api/admin/products/<pid>", methods=["DELETE"])
@admin_required
def admin_delete_product(pid):
    products_col.delete_one({"_id": ObjectId(pid)})
    return jsonify({"success": True})

@app.route("/api/admin/users")
@admin_required
def admin_users():
    users = [serialize(u) for u in users_col.find()]
    for u in users:
        u.pop("password", None)
        u["created_at"] = str(u.get("created_at",""))[:10]
        u["order_count"] = orders_col.count_documents({"customer.email": u.get("email","")})
    return jsonify(users)

# ── User Dashboard ─────────────────────────────────────
@app.route("/user")
@login_required
def user_dashboard(): return render_template("user.html")

@app.route("/api/user/orders")
@login_required
def user_orders():
    u = current_user()
    orders = [serialize(o) for o in orders_col.find({"customer.email": u["email"]}).sort("created_at",-1)]
    for o in orders: o["created_at"] = str(o.get("created_at",""))[:19]
    return jsonify(orders)

@app.route("/api/user/profile", methods=["PUT"])
@login_required
def update_profile():
    d = request.json
    uid = session["user_id"]
    upd = {"name": d["name"], "email": d["email"]}
    if d.get("password"):
        upd["password"] = hash_pw(d["password"])
    users_col.update_one({"_id": ObjectId(uid)}, {"$set": upd})
    return jsonify({"success": True})

# ── Products (public) ──────────────────────────────────
@app.route("/api/products")
def get_products():
    cat = request.args.get("category","all")
    q   = request.args.get("search","").strip()
    filt = {}
    if cat != "all": filt["category"] = cat
    if q: filt["$or"] = [{"name":{"$regex":q,"$options":"i"}},{"desc":{"$regex":q,"$options":"i"}}]
    return jsonify([serialize(p) for p in products_col.find(filt)])

@app.route("/api/products/<pid>")
def get_product(pid):
    p = products_col.find_one({"_id": ObjectId(pid)})
    return jsonify(serialize(p)) if p else (jsonify({"error":"Not found"}),404)

@app.route("/api/products/related/<pid>")
def get_related_products(pid):
    p = products_col.find_one({"_id": ObjectId(pid)})
    if not p:
        return jsonify({"error":"Not found"}), 404
    related = list(products_col.find({"category": p.get("category"), "_id": {"$ne": p["_id"]}}).limit(4))
    if len(related) < 4:
        exclude_ids = [r["_id"] for r in related] + [p["_id"]]
        extra = list(products_col.find({"_id": {"$nin": exclude_ids}}).limit(4 - len(related)))
        related.extend(extra)
    return jsonify([serialize(r) for r in related])

# ── Cart ───────────────────────────────────────────────
@app.route("/api/cart")
def get_cart():
    sid = get_session_id()
    items = list(cart_col.find({"session_id":sid}))
    result = []
    for item in items:
        p = products_col.find_one({"_id":ObjectId(item["product_id"])})
        if p:
            p = serialize(p); p["qty"]=item["qty"]; p["cart_id"]=str(item["_id"])
            result.append(p)
    return jsonify(result)

@app.route("/api/cart/add", methods=["POST"])
def add_to_cart():
    pid = request.json.get("product_id"); sid = get_session_id()
    ex  = cart_col.find_one({"session_id":sid,"product_id":pid})
    if ex: cart_col.update_one({"_id":ex["_id"]},{"$inc":{"qty":1}})
    else:  cart_col.insert_one({"session_id":sid,"product_id":pid,"qty":1})
    return jsonify({"success":True})

@app.route("/api/cart/update", methods=["POST"])
def update_cart():
    d=request.json; sid=get_session_id(); qty=int(d.get("qty",1))
    if qty<=0: cart_col.delete_one({"_id":ObjectId(d["cart_id"]),"session_id":sid})
    else: cart_col.update_one({"_id":ObjectId(d["cart_id"]),"session_id":sid},{"$set":{"qty":qty}})
    return jsonify({"success":True})

@app.route("/api/cart/remove", methods=["POST"])
def remove_from_cart():
    sid=get_session_id()
    cart_col.delete_one({"_id":ObjectId(request.json["cart_id"]),"session_id":sid})
    return jsonify({"success":True})

# ── Orders (public) ────────────────────────────────────
@app.route("/api/orders", methods=["POST"])
def place_order():
    d=request.json; sid=get_session_id()
    items=list(cart_col.find({"session_id":sid}))
    if not items: return jsonify({"error":"Cart empty"}),400
    order_items=[]; total=0
    for item in items:
        p=products_col.find_one({"_id":ObjectId(item["product_id"])})
        if p:
            price=p.get("sale_price",p["price"])
            order_items.append({"product_id":str(p["_id"]),"name":p["name"],"emoji":p["emoji"],"price":price,"qty":item["qty"],"line_total":price*item["qty"]})
            total+=price*item["qty"]
            products_col.update_one({"_id":p["_id"]},{"$inc":{"stock":-item["qty"]}})
    num="JAYA-"+str(random.randint(10000,99999))
    orders_col.insert_one({"order_number":num,"customer":d.get("customer",{}),"items":order_items,"total":total,"status":"confirmed","created_at":datetime.datetime.utcnow()})
    cart_col.delete_many({"session_id":sid})
    return jsonify({"success":True,"order_number":num,"total":total})

if __name__ == "__main__":
    seed()
    app.run(debug=True, host="0.0.0.0", port=5000, use_reloader=False)
