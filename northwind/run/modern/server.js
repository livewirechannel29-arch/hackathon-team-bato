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
const DB_PATH   = path.join(__dirname, '..', 'northwind.db');

const db  = new Database(DB_PATH);
db.pragma('journal_mode = WAL');

const app = express();
app.use(express.json());

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
// Routes
// ---------------------------------------------------------------------------

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
// Start
// ---------------------------------------------------------------------------

const PORT = 8082;
app.listen(PORT, () => {
  console.log(`Modern API running at http://localhost:${PORT}`);
  console.log(`  GET /api/orders`);
  console.log(`  GET /api/orders/:id`);
});
