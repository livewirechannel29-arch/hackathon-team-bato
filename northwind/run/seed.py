"""
Creates northwind.db (SQLite) and seeds it with sample data.
Run once: python seed.py
"""
import sqlite3, os

DB = os.path.join(os.path.dirname(__file__), "northwind.db")

sql = """
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
"""

seeds = """
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
"""

con = sqlite3.connect(DB)
con.executescript(sql)
con.executescript(seeds)
con.commit()
con.close()
print(f"Database ready: {DB}")
