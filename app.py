"""
Smart Inventory & Warehouse Tracker - Flask REST API
====================================================
Setup:
    pip install flask flask-cors mysql-connector-python PyJWT
Run:
    python app.py
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import mysql.connector
import jwt
import datetime
import functools

# ============================================================
# CONFIGURATION - Edit these to match your MySQL setup
# ============================================================

DB_CONFIG = {
    "host": "viaduct.proxy.rlwy.net",
    "user": "root",
    "password": "HnWZoalEiNjfFvAcDFCPuwDDSZRsPatg",
    "database": "railway",
    "port": 23259

}

JWT_SECRET = "warehouse_super_secret_key_2024"
JWT_ALGORITHM = "HS256"
JWT_EXPIRY_HOURS = 8

# ============================================================
# APP INIT
# ============================================================
app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}}, 
     supports_credentials=True,
     allow_headers=["Content-Type", "Authorization"])


# ============================================================
# DB HELPERS
# ============================================================
def get_db():
    return mysql.connector.connect(**DB_CONFIG)

def query(sql, params=None, fetch="all"):
    conn = get_db()
    cur = conn.cursor(dictionary=True)
    try:
        cur.execute(sql, params or ())
        if fetch == "all":
            return cur.fetchall()
        elif fetch == "one":
            return cur.fetchone()
        else:
            conn.commit()
            return cur.lastrowid or cur.rowcount
    finally:
        cur.close()
        conn.close()

def ok(data=None, msg="Success", code=200):
    return jsonify({"success": True, "message": msg, "data": data}), code

def err(msg="Error", code=400):
    return jsonify({"success": False, "message": msg}), code


# ============================================================
# AUTH HELPERS
# ============================================================
def create_token(user):
    payload = {
        "id": user["id"],
        "username": user["username"],
        "role": user["role"],
        "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=JWT_EXPIRY_HOURS),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def decode_token(token):
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

def require_auth(f):
    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        auth = request.headers.get("Authorization", "")
        if not auth.startswith("Bearer "):
            return err("Missing or invalid Authorization header", 401)
        token = auth[7:]
        payload = decode_token(token)
        if not payload:
            return err("Token expired or invalid", 401)
        request.user = payload
        return f(*args, **kwargs)
    return wrapper

def require_admin(f):
    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        if not hasattr(request, "user") or request.user.get("role") != "admin":
            return err("Admin access required", 403)
        return f(*args, **kwargs)
    return wrapper


# ============================================================
# AUTH ROUTES
# ============================================================
@app.route("/api/login", methods=["POST"])
def login():
    data = request.get_json(silent=True) or {}
    username = data.get("username", "").strip()
    password = data.get("password", "").strip()
    if not username or not password:
        return err("Username and password required")
    user = query("SELECT * FROM users WHERE username = %s AND password = %s", (username, password), fetch="one")
    if not user:
        return err("Invalid username or password", 401)
    token = create_token(user)
    return ok({
        "token": token,
        "user": {"id": user["id"], "username": user["username"], "role": user["role"]}
    }, "Login successful")

@app.route("/api/logout", methods=["POST"])
@require_auth
def logout():
    return ok(msg="Logged out successfully")


# ============================================================
# STATS ROUTE
# ============================================================
@app.route("/api/stats", methods=["GET"])
@require_auth
def stats():
    total_products = query("SELECT COUNT(*) AS c FROM product WHERE status='active'", fetch="one")["c"]
    total_warehouses = query("SELECT COUNT(*) AS c FROM warehouse WHERE status='active'", fetch="one")["c"]
    total_suppliers = query("SELECT COUNT(*) AS c FROM supplier WHERE status='active'", fetch="one")["c"]
    total_employees = query("SELECT COUNT(*) AS c FROM employee WHERE status='active'", fetch="one")["c"]
    
    stock_val = query("""
        SELECT COALESCE(SUM(s.quantity * p.unit_price), 0) AS val
        FROM stock s JOIN product p ON s.product_id = p.id
    """, fetch="one")["val"]
    
    low_stock_count = query("""
        SELECT COUNT(DISTINCT p.id) AS c
        FROM product p
        JOIN (SELECT product_id, SUM(quantity) AS total FROM stock GROUP BY product_id) agg 
            ON p.id = agg.product_id
        WHERE agg.total <= p.reorder_level
    """, fetch="one")["c"]
    
    total_orders = query("SELECT COUNT(*) AS c FROM `order`", fetch="one")["c"]
    pending_orders = query("SELECT COUNT(*) AS c FROM `order` WHERE status='pending'", fetch="one")["c"]
    bad_stock_loss = query("SELECT COALESCE(SUM(estimated_loss),0) AS v FROM bad_stock", fetch="one")["v"]
    
    return ok({
        "total_products": total_products,
        "total_warehouses": total_warehouses,
        "total_suppliers": total_suppliers,
        "total_employees": total_employees,
        "stock_value": float(stock_val),
        "low_stock_count": low_stock_count,
        "total_orders": total_orders,
        "pending_orders": pending_orders,
        "bad_stock_loss": float(bad_stock_loss),
    })


# ============================================================
# GLOBAL SEARCH
# ============================================================
@app.route("/api/search", methods=["GET"])
@require_auth
def search():
    q = request.args.get("q", "").strip()
    category = request.args.get("category", "all").lower()
    if not q:
        return ok([])
    
    like = f"%{q}%"
    results = []
    
    if category in ("all", "products"):
        rows = query("""
            SELECT id, name, sku, category, unit_price, status, 'product' AS type 
            FROM product WHERE name LIKE %s OR sku LIKE %s OR category LIKE %s
            LIMIT 10
        """, (like, like, like))
        results.extend(rows)
    
    if category in ("all", "warehouses"):
        rows = query("""
            SELECT id, name, city, state, status, 'warehouse' AS type 
            FROM warehouse WHERE name LIKE %s OR city LIKE %s OR location LIKE %s
            LIMIT 10
        """, (like, like, like))
        results.extend(rows)
    
    if category in ("all", "suppliers"):
        rows = query("""
            SELECT id, name, city, email, status, 'supplier' AS type 
            FROM supplier WHERE name LIKE %s OR city LIKE %s OR contact_person LIKE %s
            LIMIT 10
        """, (like, like, like))
        results.extend(rows)
    
    if category in ("all", "employees"):
        rows = query("""
            SELECT id, name, email, role, status, 'employee' AS type 
            FROM employee WHERE name LIKE %s OR email LIKE %s OR role LIKE %s
            LIMIT 10
        """, (like, like, like))
        results.extend(rows)
    
    return ok(results)


# ============================================================
# HISTORY (30-day restocks + orders)
# ============================================================
@app.route("/api/history", methods=["GET"])
@require_auth
def history():
    since = datetime.datetime.utcnow() - datetime.timedelta(days=30)
    
    restocks = query("""
        SELECT s.id, 'restock' AS event_type, p.name AS product_name, p.sku,
               w.name AS warehouse_name, s.quantity, s.last_restocked AS event_time,
               e.name AS done_by, s.notes
        FROM stock s
        JOIN product p ON s.product_id = p.id
        JOIN warehouse w ON s.warehouse_id = w.id
        LEFT JOIN employee e ON s.restocked_by = e.id
        WHERE s.last_restocked >= %s
        ORDER BY s.last_restocked DESC
    """, (since,))
    
    orders = query("""
        SELECT o.id, 'order' AS event_type, o.order_number, o.customer_name,
               o.status, o.total_amount, o.created_at AS event_time,
               w.name AS warehouse_name, e.name AS done_by
        FROM `order` o
        LEFT JOIN warehouse w ON o.warehouse_id = w.id
        LEFT JOIN employee e ON o.created_by = e.id
        WHERE o.created_at >= %s
        ORDER BY o.created_at DESC
    """, (since,))
    
    # Merge and sort by event_time descending
    combined = []
    for r in restocks:
        r["event_time"] = str(r.get("event_time", ""))
        combined.append(r)
    for o in orders:
        o["event_time"] = str(o.get("event_time", ""))
        combined.append(o)
    
    combined.sort(key=lambda x: x["event_time"], reverse=True)
    return ok(combined)


# ============================================================
# WAREHOUSES CRUD
# ============================================================
@app.route("/api/warehouses", methods=["GET"])
@require_auth
def get_warehouses():
    rows = query("SELECT * FROM warehouse ORDER BY id DESC")
    return ok(rows)

@app.route("/api/warehouses/<int:wid>", methods=["GET"])
@require_auth
def get_warehouse(wid):
    row = query("SELECT * FROM warehouse WHERE id=%s", (wid,), fetch="one")
    if not row: return err("Warehouse not found", 404)
    return ok(row)

@app.route("/api/warehouses", methods=["POST"])
@require_auth
def create_warehouse():
    d = request.get_json(silent=True) or {}
    required = ["name", "location", "city", "state", "capacity"]
    if not all(d.get(k) for k in required):
        return err(f"Required fields: {', '.join(required)}")
    wid = query("""
        INSERT INTO warehouse (name, location, city, state, capacity, manager_name, contact_phone, status)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
    """, (d["name"], d["location"], d["city"], d["state"], d["capacity"],
          d.get("manager_name"), d.get("contact_phone"), d.get("status", "active")), fetch="none")
    return ok({"id": wid}, "Warehouse created", 201)

@app.route("/api/warehouses/<int:wid>", methods=["PUT"])
@require_auth
def update_warehouse(wid):
    d = request.get_json(silent=True) or {}
    query("""
        UPDATE warehouse SET name=%s, location=%s, city=%s, state=%s, capacity=%s,
        manager_name=%s, contact_phone=%s, status=%s WHERE id=%s
    """, (d.get("name"), d.get("location"), d.get("city"), d.get("state"), d.get("capacity"),
          d.get("manager_name"), d.get("contact_phone"), d.get("status", "active"), wid), fetch="none")
    return ok(msg="Warehouse updated")

@app.route("/api/warehouses/<int:wid>", methods=["DELETE"])
@require_auth
def delete_warehouse(wid):
    query("DELETE FROM warehouse WHERE id=%s", (wid,), fetch="none")
    return ok(msg="Warehouse deleted")


# ============================================================
# SUPPLIERS CRUD
# ============================================================
@app.route("/api/suppliers", methods=["GET"])
@require_auth
def get_suppliers():
    rows = query("SELECT * FROM supplier ORDER BY id DESC")
    return ok(rows)

@app.route("/api/suppliers/<int:sid>", methods=["GET"])
@require_auth
def get_supplier(sid):
    row = query("SELECT * FROM supplier WHERE id=%s", (sid,), fetch="one")
    if not row: return err("Supplier not found", 404)
    return ok(row)

@app.route("/api/suppliers", methods=["POST"])
@require_auth
def create_supplier():
    d = request.get_json(silent=True) or {}
    if not d.get("name"):
        return err("Supplier name required")
    sid = query("""
        INSERT INTO supplier (name, contact_person, email, phone, address, city, country, rating, status)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
    """, (d["name"], d.get("contact_person"), d.get("email"), d.get("phone"),
          d.get("address"), d.get("city"), d.get("country", "India"),
          d.get("rating", 4.0), d.get("status", "active")), fetch="none")
    return ok({"id": sid}, "Supplier created", 201)

@app.route("/api/suppliers/<int:sid>", methods=["PUT"])
@require_auth
def update_supplier(sid):
    d = request.get_json(silent=True) or {}
    query("""
        UPDATE supplier SET name=%s, contact_person=%s, email=%s, phone=%s,
        address=%s, city=%s, country=%s, rating=%s, status=%s WHERE id=%s
    """, (d.get("name"), d.get("contact_person"), d.get("email"), d.get("phone"),
          d.get("address"), d.get("city"), d.get("country","India"),
          d.get("rating",4.0), d.get("status","active"), sid), fetch="none")
    return ok(msg="Supplier updated")

@app.route("/api/suppliers/<int:sid>", methods=["DELETE"])
@require_auth
def delete_supplier(sid):
    query("DELETE FROM supplier WHERE id=%s", (sid,), fetch="none")
    return ok(msg="Supplier deleted")


# ============================================================
# EMPLOYEES CRUD
# ============================================================
@app.route("/api/employees", methods=["GET"])
@require_auth
def get_employees():
    rows = query("""
        SELECT e.*, w.name AS warehouse_name 
        FROM employee e LEFT JOIN warehouse w ON e.warehouse_id = w.id
        ORDER BY e.id DESC
    """)
    return ok(rows)

@app.route("/api/employees/<int:eid>", methods=["GET"])
@require_auth
def get_employee(eid):
    row = query("SELECT * FROM employee WHERE id=%s", (eid,), fetch="one")
    if not row: return err("Employee not found", 404)
    return ok(row)

@app.route("/api/employees", methods=["POST"])
@require_auth
def create_employee():
    d = request.get_json(silent=True) or {}
    if not d.get("name") or not d.get("role"):
        return err("Name and role required")
    eid = query("""
        INSERT INTO employee (name, email, phone, role, warehouse_id, salary, join_date, status)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
    """, (d["name"], d.get("email"), d.get("phone"), d["role"],
          d.get("warehouse_id"), d.get("salary"), d.get("join_date"), d.get("status","active")), fetch="none")
    return ok({"id": eid}, "Employee created", 201)

@app.route("/api/employees/<int:eid>", methods=["PUT"])
@require_auth
def update_employee(eid):
    d = request.get_json(silent=True) or {}
    query("""
        UPDATE employee SET name=%s, email=%s, phone=%s, role=%s,
        warehouse_id=%s, salary=%s, join_date=%s, status=%s WHERE id=%s
    """, (d.get("name"), d.get("email"), d.get("phone"), d.get("role"),
          d.get("warehouse_id"), d.get("salary"), d.get("join_date"), d.get("status","active"), eid), fetch="none")
    return ok(msg="Employee updated")

@app.route("/api/employees/<int:eid>", methods=["DELETE"])
@require_auth
def delete_employee(eid):
    query("DELETE FROM employee WHERE id=%s", (eid,), fetch="none")
    return ok(msg="Employee deleted")


# ============================================================
# PRODUCTS CRUD
# ============================================================
@app.route("/api/products", methods=["GET"])
@require_auth
def get_products():
    rows = query("""
        SELECT p.*, s.name AS supplier_name,
               COALESCE(agg.total_qty, 0) AS total_stock
        FROM product p
        LEFT JOIN supplier s ON p.supplier_id = s.id
        LEFT JOIN (SELECT product_id, SUM(quantity) AS total_qty FROM stock GROUP BY product_id) agg
            ON p.id = agg.product_id
        ORDER BY p.id DESC
    """)
    return ok(rows)

@app.route("/api/products/<int:pid>", methods=["GET"])
@require_auth
def get_product(pid):
    row = query("SELECT * FROM product WHERE id=%s", (pid,), fetch="one")
    if not row: return err("Product not found", 404)
    return ok(row)

@app.route("/api/products", methods=["POST"])
@require_auth
def create_product():
    d = request.get_json(silent=True) or {}
    if not d.get("name") or not d.get("sku") or d.get("unit_price") is None:
        return err("Name, SKU and unit_price required")
    pid = query("""
        INSERT INTO product (name, sku, category, description, unit_price, unit, reorder_level, supplier_id, status)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
    """, (d["name"], d["sku"], d.get("category"), d.get("description"),
          d["unit_price"], d.get("unit","piece"), d.get("reorder_level",50),
          d.get("supplier_id"), d.get("status","active")), fetch="none")
    return ok({"id": pid}, "Product created", 201)

@app.route("/api/products/<int:pid>", methods=["PUT"])
@require_auth
def update_product(pid):
    d = request.get_json(silent=True) or {}
    query("""
        UPDATE product SET name=%s, sku=%s, category=%s, description=%s,
        unit_price=%s, unit=%s, reorder_level=%s, supplier_id=%s, status=%s WHERE id=%s
    """, (d.get("name"), d.get("sku"), d.get("category"), d.get("description"),
          d.get("unit_price"), d.get("unit","piece"), d.get("reorder_level",50),
          d.get("supplier_id"), d.get("status","active"), pid), fetch="none")
    return ok(msg="Product updated")

@app.route("/api/products/<int:pid>", methods=["DELETE"])
@require_auth
def delete_product(pid):
    query("DELETE FROM product WHERE id=%s", (pid,), fetch="none")
    return ok(msg="Product deleted")


# ============================================================
# STOCK CRUD
# ============================================================
@app.route("/api/stock", methods=["GET"])
@require_auth
def get_stock():
    rows = query("""
        SELECT s.*, p.name AS product_name, p.sku, p.reorder_level, p.unit_price,
               w.name AS warehouse_name, e.name AS restocked_by_name,
               (s.quantity * p.unit_price) AS stock_value,
               CASE WHEN s.quantity <= p.reorder_level THEN 1 ELSE 0 END AS is_low_stock
        FROM stock s
        JOIN product p ON s.product_id = p.id
        JOIN warehouse w ON s.warehouse_id = w.id
        LEFT JOIN employee e ON s.restocked_by = e.id
        ORDER BY is_low_stock DESC, s.id DESC
    """)
    return ok(rows)

@app.route("/api/stock/low", methods=["GET"])
@require_auth
def get_low_stock():
    rows = query("""
        SELECT p.id, p.name, p.sku, p.category, p.reorder_level, p.unit_price,
               COALESCE(SUM(s.quantity),0) AS total_quantity,
               GROUP_CONCAT(w.name SEPARATOR ', ') AS warehouses
        FROM product p
        LEFT JOIN stock s ON p.id = s.product_id
        LEFT JOIN warehouse w ON s.warehouse_id = w.id
        WHERE p.status = 'active'
        GROUP BY p.id, p.name, p.sku, p.category, p.reorder_level, p.unit_price
        HAVING total_quantity <= p.reorder_level
        ORDER BY total_quantity ASC
    """)
    return ok(rows)

@app.route("/api/stock", methods=["POST"])
@require_auth
def create_stock():
    d = request.get_json(silent=True) or {}
    if not d.get("product_id") or not d.get("warehouse_id") or d.get("quantity") is None:
        return err("product_id, warehouse_id and quantity required")
    # Upsert
    existing = query("SELECT id FROM stock WHERE product_id=%s AND warehouse_id=%s",
                     (d["product_id"], d["warehouse_id"]), fetch="one")
    if existing:
        query("""
            UPDATE stock SET quantity=%s, last_restocked=NOW(), restocked_by=%s, notes=%s
            WHERE product_id=%s AND warehouse_id=%s
        """, (d["quantity"], d.get("restocked_by"), d.get("notes"), d["product_id"], d["warehouse_id"]), fetch="none")
        return ok(msg="Stock updated (upserted)")
    else:
        sid = query("""
            INSERT INTO stock (product_id, warehouse_id, quantity, restocked_by, notes)
            VALUES (%s,%s,%s,%s,%s)
        """, (d["product_id"], d["warehouse_id"], d["quantity"],
              d.get("restocked_by"), d.get("notes")), fetch="none")
        return ok({"id": sid}, "Stock record created", 201)

@app.route("/api/stock/<int:sid>", methods=["PUT"])
@require_auth
def update_stock(sid):
    d = request.get_json(silent=True) or {}
    query("""
        UPDATE stock SET quantity=%s, last_restocked=NOW(), restocked_by=%s, notes=%s WHERE id=%s
    """, (d.get("quantity"), d.get("restocked_by"), d.get("notes"), sid), fetch="none")
    return ok(msg="Stock updated")

@app.route("/api/stock/<int:sid>", methods=["DELETE"])
@require_auth
def delete_stock(sid):
    query("DELETE FROM stock WHERE id=%s", (sid,), fetch="none")
    return ok(msg="Stock record deleted")


# ============================================================
# ORDERS CRUD
# ============================================================
@app.route("/api/orders", methods=["GET"])
@require_auth
def get_orders():
    rows = query("""
        SELECT o.*, w.name AS warehouse_name, e.name AS created_by_name,
               COUNT(oi.id) AS item_count
        FROM `order` o
        LEFT JOIN warehouse w ON o.warehouse_id = w.id
        LEFT JOIN employee e ON o.created_by = e.id
        LEFT JOIN orderitem oi ON o.id = oi.order_id
        GROUP BY o.id
        ORDER BY o.created_at DESC
    """)
    return ok(rows)

@app.route("/api/orders/<int:oid>", methods=["GET"])
@require_auth
def get_order(oid):
    order = query("SELECT * FROM `order` WHERE id=%s", (oid,), fetch="one")
    if not order: return err("Order not found", 404)
    items = query("""
        SELECT oi.*, p.name AS product_name, p.sku
        FROM orderitem oi JOIN product p ON oi.product_id = p.id
        WHERE oi.order_id = %s
    """, (oid,))
    order["items"] = items
    return ok(order)

@app.route("/api/orders", methods=["POST"])
@require_auth
def create_order():
    d = request.get_json(silent=True) or {}
    if not d.get("customer_name") or not d.get("order_number"):
        return err("customer_name and order_number required")
    oid = query("""
        INSERT INTO `order` (order_number, customer_name, customer_email, customer_phone,
        warehouse_id, status, total_amount, shipping_address, notes, created_by)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
    """, (d["order_number"], d["customer_name"], d.get("customer_email"),
          d.get("customer_phone"), d.get("warehouse_id"), d.get("status","pending"),
          d.get("total_amount",0), d.get("shipping_address"), d.get("notes"),
          d.get("created_by")), fetch="none")
    return ok({"id": oid}, "Order created", 201)

@app.route("/api/orders/<int:oid>", methods=["PUT"])
@require_auth
def update_order(oid):
    d = request.get_json(silent=True) or {}
    query("""
        UPDATE `order` SET order_number=%s, customer_name=%s, customer_email=%s,
        customer_phone=%s, warehouse_id=%s, status=%s, total_amount=%s,
        shipping_address=%s, notes=%s WHERE id=%s
    """, (d.get("order_number"), d.get("customer_name"), d.get("customer_email"),
          d.get("customer_phone"), d.get("warehouse_id"), d.get("status","pending"),
          d.get("total_amount",0), d.get("shipping_address"), d.get("notes"), oid), fetch="none")
    return ok(msg="Order updated")

@app.route("/api/orders/<int:oid>", methods=["DELETE"])
@require_auth
def delete_order(oid):
    query("DELETE FROM `order` WHERE id=%s", (oid,), fetch="none")
    return ok(msg="Order deleted")


# ============================================================
# ORDER ITEMS CRUD
# ============================================================
@app.route("/api/orderitems", methods=["GET"])
@require_auth
def get_orderitems():
    rows = query("""
        SELECT oi.*, p.name AS product_name, p.sku, o.order_number
        FROM orderitem oi
        JOIN product p ON oi.product_id = p.id
        JOIN `order` o ON oi.order_id = o.id
        ORDER BY oi.id DESC
    """)
    return ok(rows)

@app.route("/api/orderitems", methods=["POST"])
@require_auth
def create_orderitem():
    d = request.get_json(silent=True) or {}
    if not all(d.get(k) for k in ["order_id", "product_id", "quantity", "unit_price"]):
        return err("order_id, product_id, quantity, unit_price required")
    iid = query("""
        INSERT INTO orderitem (order_id, product_id, quantity, unit_price)
        VALUES (%s,%s,%s,%s)
    """, (d["order_id"], d["product_id"], d["quantity"], d["unit_price"]), fetch="none")
    return ok({"id": iid}, "Order item added", 201)

@app.route("/api/orderitems/<int:iid>", methods=["PUT"])
@require_auth
def update_orderitem(iid):
    d = request.get_json(silent=True) or {}
    query("""
        UPDATE orderitem SET quantity=%s, unit_price=%s WHERE id=%s
    """, (d.get("quantity"), d.get("unit_price"), iid), fetch="none")
    return ok(msg="Order item updated")

@app.route("/api/orderitems/<int:iid>", methods=["DELETE"])
@require_auth
def delete_orderitem(iid):
    query("DELETE FROM orderitem WHERE id=%s", (iid,), fetch="none")
    return ok(msg="Order item deleted")


# ============================================================
# BAD STOCK CRUD
# ============================================================
@app.route("/api/bad_stock", methods=["GET"])
@require_auth
def get_bad_stock():
    rows = query("""
        SELECT bs.*, p.name AS product_name, p.sku, w.name AS warehouse_name,
               e.name AS reported_by_name
        FROM bad_stock bs
        JOIN product p ON bs.product_id = p.id
        JOIN warehouse w ON bs.warehouse_id = w.id
        LEFT JOIN employee e ON bs.reported_by = e.id
        ORDER BY bs.reported_at DESC
    """)
    return ok(rows)

@app.route("/api/bad_stock/<int:bid>", methods=["GET"])
@require_auth
def get_bad_stock_item(bid):
    row = query("SELECT * FROM bad_stock WHERE id=%s", (bid,), fetch="one")
    if not row: return err("Bad stock record not found", 404)
    return ok(row)

@app.route("/api/bad_stock", methods=["POST"])
@require_auth
def create_bad_stock():
    d = request.get_json(silent=True) or {}
    if not all(d.get(k) for k in ["product_id", "warehouse_id", "quantity", "reason"]):
        return err("product_id, warehouse_id, quantity, reason required")
    bid = query("""
        INSERT INTO bad_stock (product_id, warehouse_id, quantity, reason, description,
        estimated_loss, reported_by, status)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
    """, (d["product_id"], d["warehouse_id"], d["quantity"], d["reason"],
          d.get("description"), d.get("estimated_loss"),
          d.get("reported_by"), d.get("status","reported")), fetch="none")
    return ok({"id": bid}, "Bad stock reported", 201)

@app.route("/api/bad_stock/<int:bid>", methods=["PUT"])
@require_auth
def update_bad_stock(bid):
    d = request.get_json(silent=True) or {}
    query("""
        UPDATE bad_stock SET product_id=%s, warehouse_id=%s, quantity=%s, reason=%s,
        description=%s, estimated_loss=%s, reported_by=%s, status=%s WHERE id=%s
    """, (d.get("product_id"), d.get("warehouse_id"), d.get("quantity"), d.get("reason"),
          d.get("description"), d.get("estimated_loss"), d.get("reported_by"),
          d.get("status","reported"), bid), fetch="none")
    return ok(msg="Bad stock updated")

@app.route("/api/bad_stock/<int:bid>", methods=["DELETE"])
@require_auth
def delete_bad_stock(bid):
    query("DELETE FROM bad_stock WHERE id=%s", (bid,), fetch="none")
    return ok(msg="Bad stock record deleted")


# ============================================================
# USERS (admin only)
# ============================================================
@app.route("/api/users", methods=["GET"])
@require_auth
def get_users():
    rows = query("SELECT id, username, role, created_at FROM users ORDER BY id")
    return ok(rows)

@app.route("/api/users", methods=["POST"])
@require_auth
def create_user():
    d = request.get_json(silent=True) or {}
    if not d.get("username") or not d.get("password"):
        return err("Username and password required")
    uid = query("INSERT INTO users (username, password, role) VALUES (%s,%s,%s)",
                (d["username"], d["password"], d.get("role","staff")), fetch="none")
    return ok({"id": uid}, "User created", 201)

@app.route("/api/users/<int:uid>", methods=["DELETE"])
@require_auth
def delete_user(uid):
    query("DELETE FROM users WHERE id=%s", (uid,), fetch="none")
    return ok(msg="User deleted")


# ============================================================
# RUN
# ============================================================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)