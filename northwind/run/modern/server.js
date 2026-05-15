/**
 * Northwind Logistics — modern API  (first extracted routes)
 *
 * Runs alongside the legacy server. Handles only the routes
 * that have been migrated. Everything else still goes to legacy.
 *
 * Port: 8082
 */

import express from 'express';
import Database from 'better-sqlite3';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

const db = new Database(':memory:');
db.pragma('journal_mode = WAL');

db.exec(`
  CREATE TABLE IF NOT EXISTS employees (
    employee_id INTEGER PRIMARY KEY AUTOINCREMENT,
    username    TEXT NOT NULL UNIQUE,
    password    TEXT NOT NULL,
    first_name  TEXT NOT NULL,
    last_name   TEXT NOT NULL,
    role        TEXT NOT NULL DEFAULT 'handler',
    active      INTEGER NOT NULL DEFAULT 1
  );
  CREATE TABLE IF NOT EXISTS customers (
    customer_id  INTEGER PRIMARY KEY AUTOINCREMENT,
    company_name TEXT NOT NULL,
    contact_name TEXT,
    email        TEXT,
    phone        TEXT,
    address      TEXT,
    city         TEXT,
    country      TEXT
  );
  CREATE TABLE IF NOT EXISTS suppliers (
    supplier_id  INTEGER PRIMARY KEY AUTOINCREMENT,
    company_name TEXT NOT NULL,
    contact_name TEXT,
    email        TEXT,
    phone        TEXT
  );
  CREATE TABLE IF NOT EXISTS products (
    product_id     INTEGER PRIMARY KEY AUTOINCREMENT,
    product_name   TEXT NOT NULL,
    supplier_id    INTEGER,
    category       TEXT,
    unit_price     REAL NOT NULL DEFAULT 0,
    units_in_stock INTEGER NOT NULL DEFAULT 0
  );
  CREATE TABLE IF NOT EXISTS orders (
    order_id    INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id INTEGER NOT NULL,
    employee_id INTEGER NOT NULL,
    order_date  TEXT NOT NULL,
    ship_date   TEXT,
    status      TEXT NOT NULL DEFAULT 'pending',
    note        TEXT
  );
  CREATE TABLE IF NOT EXISTS order_items (
    item_id    INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id   INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    quantity   INTEGER NOT NULL DEFAULT 1,
    unit_price REAL NOT NULL
  );

  INSERT OR IGNORE INTO employees (username,password,first_name,last_name,role) VALUES
    ('admin','admin123','Gary','Chen','admin'),
    ('steve','steve','Steve','Kowalski','handler'),
    ('viewer','view','Sally','Marsh','viewer');

  INSERT OR IGNORE INTO suppliers VALUES
    (1,'Pacific Freight Co.','Tom Li','tom@pacificfreight.example','555-0101'),
    (2,'Heartland Goods Ltd.','Maria Garcia','mgarcia@heartland.example','555-0202'),
    (3,'Eastern Trade Partners','Ahmed Nasser','ahmed@eastern-trade.example','555-0303');

  INSERT OR IGNORE INTO customers VALUES
    (1,'Oceanic Airlines','Laura Petrov','lpetrov@oceanic.example','555-1001','100 Airport Blvd','Sydney','Australia'),
    (2,'Acme Corp.','John Smith','jsmith@acme.example','555-1002','42 Industry Lane','Chicago','USA'),
    (3,'Globex Corp.','Hank Scorpio','hscorpio@globex.example','555-1003','1 Globex Way','Cypress Creek','USA'),
    (4,'Initech','Bill Lumbergh','blumbergh@initech.example','555-1004','15 Corporate Dr.','Dallas','USA'),
    (5,'Umbrella Trading','Alice Wong','awong@umbrella.example','555-1005','8 Commerce St.','Hong Kong','China');

  INSERT OR IGNORE INTO products VALUES
    (1,'Heavy Freight Crate',1,'Packaging',12.50,150),
    (2,'Climate Box (Cold)',1,'Packaging',48.00,42),
    (3,'Standard Pallet',2,'Packaging',8.75,300),
    (4,'Fragile Item Wrap',2,'Packaging',3.20,87),
    (5,'Hazmat Container L1',3,'Hazmat',120.00,8),
    (6,'Express Courier Label',1,'Labeling',1.50,1000),
    (7,'Refrigerated Container',1,'Cold Chain',350.00,4),
    (8,'Document Envelope',2,'Labeling',0.75,2000);

  INSERT OR IGNORE INTO orders (order_id,customer_id,employee_id,order_date,ship_date,status,note) VALUES
    (1,1,2,'2024-01-15 09:00','2024-01-18 14:00','shipped','Handle with care, priority client'),
    (2,2,2,'2024-01-22 11:30',NULL,'pending',NULL),
    (3,3,2,'2024-02-01 08:00','2024-02-03 12:00','shipped','Fragile contents'),
    (4,4,2,'2024-02-10 14:00',NULL,'cancelled','Customer cancelled — duplicate order'),
    (5,5,2,'2024-02-14 10:00',NULL,'pending','Requires customs clearance'),
    (6,1,2,'2024-03-01 09:00',NULL,'pending',NULL);

  INSERT OR IGNORE INTO order_items (order_id,product_id,quantity,unit_price) VALUES
    (1,1,10,12.50),(1,6,100,1.50),
    (2,3,5,8.75),(2,4,20,3.20),
    (3,2,2,48.00),(3,5,1,120.00),
    (4,1,3,12.50),
    (5,7,1,350.00),(5,5,2,120.00),
    (6,8,50,0.75),(6,6,200,1.50);
`);

const app = express();
app.use(express.json());
app.use(express.static(path.join(__dirname, 'public')));

// ---------------------------------------------------------------------------
// Repository — all SQL uses prepared statements, named params
// ---------------------------------------------------------------------------

const OrderRepository = {
  list(status = '', customerId = 0) {
    const conditions = ['1=1'];
    const params     = {};

    if (status) {
      conditions.push('o.status = $status');
      params.$status = status;
    }
    if (customerId > 0) {
      conditions.push('o.customer_id = $customerId');
      params.$customerId = customerId;
    }

    const sql = `
      SELECT o.order_id, o.order_date, o.ship_date, o.status,
             c.company_name, c.customer_id,
             e.first_name, e.last_name,
             COUNT(oi.item_id)                              AS item_count,
             COALESCE(SUM(oi.quantity * oi.unit_price), 0)  AS total
      FROM orders o
      JOIN customers   c  ON o.customer_id = c.customer_id
      JOIN employees   e  ON o.employee_id = e.employee_id
      LEFT JOIN order_items oi ON o.order_id = oi.order_id
      WHERE ${conditions.join(' AND ')}
      GROUP BY o.order_id
      ORDER BY o.order_date DESC
      LIMIT 200`;

    return db.prepare(sql).all(params);
  },

  findById(id) {
    const order = db.prepare(`
      SELECT o.*, c.company_name, c.contact_name, c.email, c.phone,
             e.first_name, e.last_name
      FROM orders o
      JOIN customers c ON o.customer_id = c.customer_id
      JOIN employees e ON o.employee_id = e.employee_id
      WHERE o.order_id = ?`).get(id);

    if (!order) return null;

    order.items = db.prepare(`
      SELECT oi.*, p.product_name
      FROM order_items oi
      JOIN products p ON oi.product_id = p.product_id
      WHERE oi.order_id = ?`).all(id);

    return order;
  },
};

// ---------------------------------------------------------------------------
// Repositories
// ---------------------------------------------------------------------------

const CustomerRepository = {
  list() {
    return db.prepare(`
      SELECT c.*,
             COUNT(DISTINCT o.order_id) AS order_count
      FROM customers c
      LEFT JOIN orders o ON c.customer_id = o.customer_id
      GROUP BY c.customer_id
      ORDER BY c.company_name`).all();
  },
  findById(id) {
    const customer = db.prepare(`SELECT * FROM customers WHERE customer_id = ?`).get(id);
    if (!customer) return null;
    customer.orders = db.prepare(`
      SELECT o.order_id, o.order_date, o.ship_date, o.status,
             e.first_name, e.last_name,
             COUNT(oi.item_id) AS item_count,
             COALESCE(SUM(oi.quantity * oi.unit_price), 0) AS total
      FROM orders o
      JOIN employees e ON o.employee_id = e.employee_id
      LEFT JOIN order_items oi ON o.order_id = oi.order_id
      WHERE o.customer_id = ?
      GROUP BY o.order_id
      ORDER BY o.order_date DESC`).all(id);
    return customer;
  },
};

const ProductRepository = {
  list() {
    return db.prepare(`
      SELECT p.*, s.company_name AS supplier_name
      FROM products p
      LEFT JOIN suppliers s ON p.supplier_id = s.supplier_id
      ORDER BY p.category, p.product_name`).all();
  },
  findById(id) {
    return db.prepare(`
      SELECT p.*, s.company_name AS supplier_name, s.contact_name AS supplier_contact,
             s.email AS supplier_email, s.phone AS supplier_phone
      FROM products p
      LEFT JOIN suppliers s ON p.supplier_id = s.supplier_id
      WHERE p.product_id = ?`).get(id);
  },
};

// ---------------------------------------------------------------------------
// Routes
// ---------------------------------------------------------------------------

app.get('/api/customers', (req, res) => {
  res.json({ data: CustomerRepository.list() });
});

app.get('/api/customers/:id(\\d+)', (req, res) => {
  const customer = CustomerRepository.findById(Number(req.params.id));
  if (!customer) return res.status(404).json({ error: 'Customer not found' });
  res.json(customer);
});

app.get('/api/products', (req, res) => {
  res.json({ data: ProductRepository.list() });
});

app.get('/api/products/:id(\\d+)', (req, res) => {
  const product = ProductRepository.findById(Number(req.params.id));
  if (!product) return res.status(404).json({ error: 'Product not found' });
  res.json(product);
});

app.get('/api/reports', (req, res) => {
  const summary = db.prepare(`
    SELECT
      COUNT(*)                                          AS total_orders,
      COALESCE(SUM(oi.quantity * oi.unit_price), 0)    AS total_revenue,
      COALESCE(AVG(order_totals.total), 0)             AS avg_order_value,
      COUNT(CASE WHEN o.status = 'shipped'   THEN 1 END) AS shipped,
      COUNT(CASE WHEN o.status = 'pending'   THEN 1 END) AS pending,
      COUNT(CASE WHEN o.status = 'cancelled' THEN 1 END) AS cancelled
    FROM orders o
    LEFT JOIN order_items oi ON o.order_id = oi.order_id
    LEFT JOIN (
      SELECT order_id, SUM(quantity * unit_price) AS total FROM order_items GROUP BY order_id
    ) order_totals ON o.order_id = order_totals.order_id`).get();

  const byMonth = db.prepare(`
    SELECT strftime('%Y-%m', o.order_date) AS month,
           COUNT(*)                        AS order_count,
           COALESCE(SUM(oi.quantity * oi.unit_price), 0) AS revenue
    FROM orders o
    LEFT JOIN order_items oi ON o.order_id = oi.order_id
    GROUP BY month
    ORDER BY month`).all();

  const topCustomers = db.prepare(`
    SELECT c.company_name,
           COUNT(DISTINCT o.order_id)                AS order_count,
           COALESCE(SUM(oi.quantity * oi.unit_price), 0) AS total_spend
    FROM customers c
    JOIN orders o ON c.customer_id = o.customer_id
    LEFT JOIN order_items oi ON o.order_id = oi.order_id
    GROUP BY c.customer_id
    ORDER BY total_spend DESC
    LIMIT 5`).all();

  const topProducts = db.prepare(`
    SELECT p.product_name, p.category,
           COALESCE(SUM(oi.quantity), 0)             AS units_sold,
           COALESCE(SUM(oi.quantity * oi.unit_price), 0) AS revenue
    FROM products p
    LEFT JOIN order_items oi ON p.product_id = oi.product_id
    GROUP BY p.product_id
    ORDER BY revenue DESC
    LIMIT 5`).all();

  const byCategory = db.prepare(`
    SELECT p.category,
           COALESCE(SUM(oi.quantity * oi.unit_price), 0) AS revenue,
           COALESCE(SUM(oi.quantity), 0) AS units_sold
    FROM products p
    LEFT JOIN order_items oi ON p.product_id = oi.product_id
    WHERE p.category IS NOT NULL
    GROUP BY p.category
    ORDER BY revenue DESC`).all();

  res.json({ summary, byMonth, topCustomers, topProducts, byCategory });
});

app.get('/api/orders', (req, res) => {
  const status     = req.query.status      ?? '';
  const customerId = Number(req.query.customer_id ?? 0);
  const orders     = OrderRepository.list(status, customerId);
  res.json({ data: orders, count: orders.length });
});

app.get('/api/orders/:id(\\d+)', (req, res) => {
  const order = OrderRepository.findById(Number(req.params.id));
  if (!order) return res.status(404).json({ error: 'Order not found' });
  res.json(order);
});

// ---------------------------------------------------------------------------
// Start (local dev only — Vercel uses the default export)
// ---------------------------------------------------------------------------

if (process.env.NODE_ENV !== 'production') {
  const PORT = 8082;
  app.listen(PORT, () => {
    console.log(`Modern API running at http://localhost:${PORT}`);
  });
}

export default app;
