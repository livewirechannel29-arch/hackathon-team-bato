"""
Northwind Logistics — legacy monolith  (Python edition of the PHP 5 original)

Same sins:
  - SQL built by string concatenation → injection risk
  - Session stored in a plain dict keyed by a cookie value
  - All logic in one file: routing, SQL, HTML generation
  - No error handling ("if it breaks, call IT at x4400")

Run: python legacy_server.py
"""
import http.server, urllib.parse, sqlite3, html, os, uuid, json
from datetime import datetime

DB      = os.path.join(os.path.dirname(__file__), "northwind.db")
PORT    = 8081
SESSIONS = {}  # global dict — "session in globals"


# ---- helpers ---------------------------------------------------------------

def db():
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    return con


def session_get(cookie_header):
    for part in (cookie_header or "").split(";"):
        k, _, v = part.strip().partition("=")
        if k == "sid":
            return SESSIONS.get(v, {}), v
    new_id = str(uuid.uuid4())
    return {}, new_id


def q(s):
    return html.escape(str(s) if s else "")


def sql_concat_query(status_filter, cid_filter):
    # intentional string concatenation — this is the legacy smell we're showing
    sql = """SELECT o.order_id, o.order_date, o.ship_date, o.status,
                    c.company_name, c.customer_id,
                    e.first_name, e.last_name,
                    COUNT(oi.item_id) AS item_count,
                    COALESCE(SUM(oi.quantity * oi.unit_price), 0) AS total
             FROM orders o
             JOIN customers c    ON o.customer_id = c.customer_id
             JOIN employees e    ON o.employee_id = e.employee_id
             LEFT JOIN order_items oi ON o.order_id = oi.order_id
             WHERE 1=1"""
    if status_filter:
        sql += f" AND o.status = '{status_filter}'"   # ← injection
    if cid_filter:
        sql += f" AND o.customer_id = {cid_filter}"   # ← injection
    sql += " GROUP BY o.order_id ORDER BY o.order_date DESC LIMIT 200"
    return sql


# ---- HTML fragments --------------------------------------------------------

CSS = """
<style>
body  { font-family: Verdana, sans-serif; font-size: 13px; background: #f0f0f0; margin: 0; }
#hdr  { background: #003366; color: white; padding: 8px 16px; }
#hdr a{ color: #aad4ff; text-decoration: none; margin-right: 16px; }
#wrap { padding: 16px; }
table { border-collapse: collapse; width: 100%; background: white; }
th    { background: #336699; color: white; padding: 6px 10px; text-align: left; }
td    { padding: 5px 10px; border-bottom: 1px solid #ddd; }
tr:hover td { background: #eef4ff; }
.btn  { background: #336699; color: white; border: none; padding: 5px 12px; cursor: pointer; }
.msg  { background: #ddffdd; border: 1px solid #99cc99; padding: 6px 10px; margin-bottom: 12px; }
.err  { background: #ffdddd; border: 1px solid #cc9999; padding: 6px 10px; margin-bottom: 12px; }
.status-pending   { color: #996600; font-weight: bold; }
.status-shipped   { color: #006600; font-weight: bold; }
.status-cancelled { color: #990000; font-weight: bold; }
</style>
"""

def header(sess):
    uname = q(sess.get("uname", ""))
    role  = sess.get("role", "")
    nav   = f"""<div id="hdr">
    <strong>Northwind Logistics</strong> &nbsp;|&nbsp;
    <a href="/?page=orders">Orders</a>
    <a href="/?page=customers">Customers</a>
    <a href="/?page=products">Products</a>
    {"<a href='/?page=reports'>Reports</a>" if role == "admin" else ""}
    &nbsp;&nbsp; logged in as <strong>{uname}</strong>
    &nbsp; <a href="/?logout=1">Logout</a>
</div>"""
    return nav


def page_wrap(body, sess=None, show_nav=True):
    nav = header(sess) if (show_nav and sess) else ""
    return f"<!DOCTYPE html><html><head><title>Northwind Logistics</title>{CSS}</head><body>{nav}<div id='wrap'>{body}</div></body></html>"


# ---- page renderers --------------------------------------------------------

def page_login(error=""):
    err = f'<div class="err">{q(error)}</div>' if error else ""
    return page_wrap(f"""
    <h2>Northwind Logistics — Sign In</h2>{err}
    <form method="post" action="/">
        <input type="hidden" name="action" value="login">
        <table style="width:300px">
            <tr><td>Username</td><td><input name="username" type="text" style="width:160px"></td></tr>
            <tr><td>Password</td><td><input name="password" type="password" style="width:160px"></td></tr>
            <tr><td colspan="2" style="padding-top:8px"><button class="btn">Login</button></td></tr>
        </table>
    </form>""", show_nav=False)


def page_orders(sess, qs):
    status_filter = qs.get("status", [""])[0]
    cid_filter    = qs.get("customer_id", ["0"])[0]
    try:
        cid_filter = int(cid_filter)
    except ValueError:
        cid_filter = 0

    con  = db()
    rows = con.execute(sql_concat_query(status_filter, cid_filter)).fetchall()
    con.close()

    rows_html = ""
    for r in rows:
        ship = q(r["ship_date"]) if r["ship_date"] else "—"
        rows_html += f"""<tr>
            <td>{r['order_id']}</td>
            <td><a href="/?page=customers&id={r['customer_id']}">{q(r['company_name'])}</a></td>
            <td>{q(r['first_name'])} {q(r['last_name'])}</td>
            <td>{q(r['order_date'])}</td><td>{ship}</td>
            <td>{r['item_count']}</td>
            <td>${r['total']:.2f}</td>
            <td><span class="status-{r['status']}">{r['status'].capitalize()}</span></td>
            <td><a href="/?page=order_detail&id={r['order_id']}">View</a></td>
        </tr>"""

    body = f"""<h2>Orders</h2>
    <p>Filter:
        <a href="/?page=orders">All</a> |
        <a href="/?page=orders&status=pending">Pending</a> |
        <a href="/?page=orders&status=shipped">Shipped</a> |
        <a href="/?page=orders&status=cancelled">Cancelled</a>
    </p>
    <table><tr><th>#</th><th>Customer</th><th>Handler</th><th>Order Date</th>
    <th>Ship Date</th><th>Items</th><th>Total</th><th>Status</th><th></th></tr>
    {rows_html}</table>"""
    return page_wrap(body, sess)


def page_order_detail(sess, qs, msg=""):
    oid = int(qs.get("id", ["0"])[0])
    con = db()
    # string-concatenated, same as the PHP original
    order = con.execute(
        f"SELECT o.*, c.company_name, c.contact_name, c.email, c.phone,"
        f" e.first_name, e.last_name FROM orders o"
        f" JOIN customers c ON o.customer_id=c.customer_id"
        f" JOIN employees e ON o.employee_id=e.employee_id"
        f" WHERE o.order_id={oid}"
    ).fetchone()
    items = con.execute(
        f"SELECT oi.*, p.product_name FROM order_items oi"
        f" JOIN products p ON oi.product_id=p.product_id"
        f" WHERE oi.order_id={oid}"
    ).fetchall()
    con.close()

    if not order:
        return page_wrap("<p>Order not found.</p>", sess)

    msg_html = '<div class="msg">Order marked as shipped.</div>' if msg == "shipped" else ""
    items_html = ""
    grand = 0
    for it in items:
        sub = it["quantity"] * it["unit_price"]
        grand += sub
        items_html += f"<tr><td>{q(it['product_name'])}</td><td>{it['quantity']}</td><td>${it['unit_price']:.2f}</td><td>${sub:.2f}</td></tr>"

    ship_btn = ""
    if order["status"] == "pending" and sess.get("role") != "viewer":
        ship_btn = f"""<form method="post" action="/"><input type="hidden" name="action" value="ship_order">
            <input type="hidden" name="order_id" value="{oid}">
            <button class="btn">Mark as Shipped</button></form>"""

    body = f"""{msg_html}<h2>Order #{oid}</h2>
    <table style="width:500px;margin-bottom:16px">
        <tr><th colspan="2">Order Info</th></tr>
        <tr><td>Customer</td><td>{q(order['company_name'])} ({q(order['contact_name'])})</td></tr>
        <tr><td>Email</td><td>{q(order['email'])}</td></tr>
        <tr><td>Handler</td><td>{q(order['first_name'])} {q(order['last_name'])}</td></tr>
        <tr><td>Order Date</td><td>{q(order['order_date'])}</td></tr>
        <tr><td>Ship Date</td><td>{q(order['ship_date']) if order['ship_date'] else 'Not shipped'}</td></tr>
        <tr><td>Status</td><td><span class="status-{order['status']}">{order['status'].capitalize()}</span></td></tr>
        <tr><td>Note</td><td>{q(order['note'])}</td></tr>
    </table>
    <h3>Line Items</h3>
    <table><tr><th>Product</th><th>Qty</th><th>Unit Price</th><th>Subtotal</th></tr>
    {items_html}
    <tr><td colspan="3"><strong>Total</strong></td><td><strong>${grand:.2f}</strong></td></tr>
    </table><p>{ship_btn}</p><p><a href="/?page=orders">← Back to Orders</a></p>"""
    return page_wrap(body, sess)


def page_customers(sess, qs):
    cid = qs.get("id", [""])[0]
    con = db()
    if cid:
        cid = int(cid)
        cust = con.execute(f"SELECT * FROM customers WHERE customer_id={cid}").fetchone()
        ords = con.execute(
            f"SELECT o.order_id, o.order_date, o.status,"
            f" COALESCE((SELECT SUM(quantity*unit_price) FROM order_items WHERE order_id=o.order_id),0) AS total"
            f" FROM orders o WHERE customer_id={cid} ORDER BY order_date DESC"
        ).fetchall()
        con.close()
        rows = "".join(
            f"<tr><td>{o['order_id']}</td><td>{q(o['order_date'])}</td>"
            f"<td><span class='status-{o['status']}'>{o['status'].capitalize()}</span></td>"
            f"<td>${o['total']:.2f}</td>"
            f"<td><a href='/?page=order_detail&id={o['order_id']}'>View</a></td></tr>"
            for o in ords
        )
        body = f"""<h2>Customer: {q(cust['company_name'])}</h2>
        <form method="post" action="/">
            <input type="hidden" name="action" value="update_customer">
            <input type="hidden" name="customer_id" value="{cid}">
            <table style="width:420px;margin-bottom:16px">
                <tr><td>Contact</td><td>{q(cust['contact_name'])}</td></tr>
                <tr><td>Email</td><td><input name="email" value="{q(cust['email'])}" style="width:220px"></td></tr>
                <tr><td>Phone</td><td><input name="phone" value="{q(cust['phone'])}" style="width:140px"></td></tr>
                <tr><td colspan="2"><button class="btn">Save</button></td></tr>
            </table>
        </form>
        <h3>Order History</h3>
        <table><tr><th>#</th><th>Date</th><th>Status</th><th>Total</th><th></th></tr>{rows}</table>
        <p><a href="/?page=customers">← All Customers</a></p>"""
    else:
        rows_data = con.execute(
            "SELECT c.*, COUNT(o.order_id) AS order_count FROM customers c"
            " LEFT JOIN orders o ON c.customer_id=o.customer_id"
            " GROUP BY c.customer_id ORDER BY c.company_name"
        ).fetchall()
        con.close()
        rows = "".join(
            f"<tr><td>{q(r['company_name'])}</td><td>{q(r['contact_name'])}</td>"
            f"<td>{q(r['city'])}</td><td>{q(r['country'])}</td><td>{r['order_count']}</td>"
            f"<td><a href='/?page=customers&id={r['customer_id']}'>Edit</a></td></tr>"
            for r in rows_data
        )
        body = f"""<h2>Customers</h2>
        <table><tr><th>Company</th><th>Contact</th><th>City</th><th>Country</th><th>Orders</th><th></th></tr>
        {rows}</table>"""
    return page_wrap(body, sess)


def page_products(sess):
    con  = db()
    rows_data = con.execute(
        "SELECT p.*, s.company_name AS supplier_name FROM products p"
        " JOIN suppliers s ON p.supplier_id=s.supplier_id ORDER BY p.product_name"
    ).fetchall()
    con.close()
    rows = ""
    for r in rows_data:
        stock = f"<strong style='color:red'>{r['units_in_stock']} LOW</strong>" if r["units_in_stock"] <= 10 else str(r["units_in_stock"])
        rows += f"<tr><td>{q(r['product_name'])}</td><td>{q(r['category'])}</td><td>{q(r['supplier_name'])}</td><td>${r['unit_price']:.2f}</td><td>{stock}</td></tr>"
    body = f"""<h2>Products</h2>
    <table><tr><th>Product</th><th>Category</th><th>Supplier</th><th>Price</th><th>In Stock</th></tr>{rows}</table>"""
    return page_wrap(body, sess)


def page_reports(sess):
    if sess.get("role") != "admin":
        return page_wrap('<p class="err">Access denied.</p>', sess)
    con  = db()
    rows_data = con.execute(
        "SELECT strftime('%Y-%m', o.order_date) AS month,"
        " COUNT(DISTINCT o.order_id) AS orders,"
        " COALESCE(SUM(oi.quantity * oi.unit_price), 0) AS revenue"
        " FROM orders o LEFT JOIN order_items oi ON o.order_id=oi.order_id"
        " WHERE o.status != 'cancelled'"
        " GROUP BY month ORDER BY month DESC LIMIT 24"
    ).fetchall()
    con.close()
    rows = "".join(
        f"<tr><td>{r['month']}</td><td>{r['orders']}</td><td>${r['revenue']:.2f}</td></tr>"
        for r in rows_data
    )
    body = f"""<h2>Monthly Revenue</h2>
    <table style="width:360px"><tr><th>Month</th><th>Orders</th><th>Revenue</th></tr>{rows}</table>"""
    return page_wrap(body, sess)


# ---- request handler -------------------------------------------------------

class Handler(http.server.BaseHTTPRequestHandler):

    def log_message(self, fmt, *args):
        print(f"[legacy] {self.address_string()} {fmt % args}")

    def send_html(self, body, status=200, cookie=None):
        encoded = body.encode()
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        if cookie:
            self.send_header("Set-Cookie", f"sid={cookie}; Path=/; HttpOnly")
        self.end_headers()
        self.wfile.write(encoded)

    def redirect(self, url, cookie=None):
        self.send_response(302)
        self.send_header("Location", url)
        if cookie:
            self.send_header("Set-Cookie", f"sid={cookie}; Path=/; HttpOnly")
        self.end_headers()

    def read_body(self):
        length = int(self.headers.get("Content-Length", 0))
        raw    = self.rfile.read(length).decode()
        return urllib.parse.parse_qs(raw)

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        qs     = urllib.parse.parse_qs(parsed.query)
        sess, sid = session_get(self.headers.get("Cookie", ""))

        if qs.get("logout"):
            SESSIONS.pop(sid, None)
            self.redirect("/?page=login")
            return

        page = qs.get("page", ["orders"])[0]

        if page != "login" and not sess.get("uid"):
            self.redirect("/?page=login")
            return

        if page == "orders":
            self.send_html(page_orders(sess, qs))
        elif page == "order_detail":
            msg = qs.get("msg", [""])[0]
            self.send_html(page_order_detail(sess, qs, msg))
        elif page == "customers":
            self.send_html(page_customers(sess, qs))
        elif page == "products":
            self.send_html(page_products(sess))
        elif page == "reports":
            self.send_html(page_reports(sess))
        elif page == "login":
            self.send_html(page_login(), cookie=sid if sid not in SESSIONS else None)
        else:
            self.send_html(page_wrap("<p>Page not found.</p>", sess))

    def do_POST(self):
        body  = self.read_body()
        sess, sid = session_get(self.headers.get("Cookie", ""))
        action = body.get("action", [""])[0]

        if action == "login":
            username = body.get("username", [""])[0]
            password = body.get("password", [""])[0]
            # string concatenation — the whole point
            sql = f"SELECT * FROM employees WHERE username='{username}' AND password='{password}' AND active=1"
            con = db()
            emp = con.execute(sql).fetchone()
            con.close()
            if emp:
                SESSIONS[sid] = {"uid": emp["employee_id"], "uname": emp["first_name"] + " " + emp["last_name"], "role": emp["role"]}
                self.redirect("/?page=orders", cookie=sid)
            else:
                self.send_html(page_login("Bad username or password."), cookie=sid)
            return

        if not sess.get("uid"):
            self.redirect("/?page=login")
            return

        if action == "ship_order":
            oid = int(body.get("order_id", ["0"])[0])
            con = db()
            con.execute(f"UPDATE orders SET status='shipped', ship_date=datetime('now') WHERE order_id={oid}")
            con.commit()
            con.close()
            self.redirect(f"/?page=order_detail&id={oid}&msg=shipped")
            return

        if action == "update_customer":
            cid   = int(body.get("customer_id", ["0"])[0])
            email = body.get("email", [""])[0]
            phone = body.get("phone", [""])[0]
            con   = db()
            con.execute(f"UPDATE customers SET email='{email}', phone='{phone}' WHERE customer_id={cid}")
            con.commit()
            con.close()
            self.redirect("/?page=customers&msg=saved")
            return

        self.redirect("/")


if __name__ == "__main__":
    print(f"Legacy monolith running at http://localhost:{PORT}")
    print("Login: admin / admin123")
    http.server.HTTPServer(("", PORT), Handler).serve_forever()
