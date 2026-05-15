-- Northwind Logistics — database schema
-- MySQL 5.x  (don't upgrade, Gary said so)
-- last touched by Steve K. ~2011

CREATE TABLE IF NOT EXISTS employees (
    employee_id   INT          AUTO_INCREMENT PRIMARY KEY,
    username      VARCHAR(50)  NOT NULL UNIQUE,
    password      VARCHAR(100) NOT NULL,        -- plaintext, yes really, "nobody outside can access this anyway"
    first_name    VARCHAR(50)  NOT NULL,
    last_name     VARCHAR(50)  NOT NULL,
    role          ENUM('admin','handler','viewer') NOT NULL DEFAULT 'handler',
    active        TINYINT(1)   NOT NULL DEFAULT 1,
    hired_date    DATE
);

CREATE TABLE IF NOT EXISTS customers (
    customer_id   INT          AUTO_INCREMENT PRIMARY KEY,
    company_name  VARCHAR(100) NOT NULL,
    contact_name  VARCHAR(100),
    email         VARCHAR(100),
    phone         VARCHAR(30),
    address       VARCHAR(200),
    city          VARCHAR(60),
    country       VARCHAR(60),
    created_at    DATETIME     DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS suppliers (
    supplier_id   INT          AUTO_INCREMENT PRIMARY KEY,
    company_name  VARCHAR(100) NOT NULL,
    contact_name  VARCHAR(100),
    email         VARCHAR(100),
    phone         VARCHAR(30)
);

CREATE TABLE IF NOT EXISTS products (
    product_id      INT           AUTO_INCREMENT PRIMARY KEY,
    product_name    VARCHAR(100)  NOT NULL,
    supplier_id     INT,
    category        VARCHAR(60),
    unit_price      DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    units_in_stock  INT           NOT NULL DEFAULT 0,
    FOREIGN KEY (supplier_id) REFERENCES suppliers(supplier_id)
);

CREATE TABLE IF NOT EXISTS orders (
    order_id      INT          AUTO_INCREMENT PRIMARY KEY,
    customer_id   INT          NOT NULL,
    employee_id   INT          NOT NULL,
    order_date    DATETIME     NOT NULL DEFAULT NOW(),
    ship_date     DATETIME,
    status        ENUM('pending','shipped','cancelled') NOT NULL DEFAULT 'pending',
    note          TEXT,
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id),
    FOREIGN KEY (employee_id) REFERENCES employees(employee_id)
);

CREATE TABLE IF NOT EXISTS order_items (
    item_id       INT           AUTO_INCREMENT PRIMARY KEY,
    order_id      INT           NOT NULL,
    product_id    INT           NOT NULL,
    quantity      INT           NOT NULL DEFAULT 1,
    unit_price    DECIMAL(10,2) NOT NULL,
    FOREIGN KEY (order_id)   REFERENCES orders(order_id),
    FOREIGN KEY (product_id) REFERENCES products(product_id)
);

-- ---- seed data ----

INSERT INTO employees (username, password, first_name, last_name, role) VALUES
    ('admin',  'admin123', 'Gary',  'Chen',     'admin'),
    ('steve',  'steve',    'Steve', 'Kowalski',  'handler'),
    ('viewer', 'view',     'Sally', 'Marsh',     'viewer');

INSERT INTO suppliers VALUES
    (1, 'Pacific Freight Co.',    'Tom Li',       'tom@pacificfreight.example',  '555-0101'),
    (2, 'Heartland Goods Ltd.',   'Maria Garcia', 'mgarcia@heartland.example',   '555-0202'),
    (3, 'Eastern Trade Partners', 'Ahmed Nasser', 'ahmed@eastern-trade.example', '555-0303');

INSERT INTO customers VALUES
    (1, 'Oceanic Airlines',  'Laura Petrov',  'lpetrov@oceanic.example',   '555-1001', '100 Airport Blvd',  'Sydney',       'Australia', NOW()),
    (2, 'Acme Corp.',        'John Smith',    'jsmith@acme.example',       '555-1002', '42 Industry Lane',  'Chicago',      'USA',       NOW()),
    (3, 'Globex Corp.',      'Hank Scorpio',  'hscorpio@globex.example',   '555-1003', '1 Globex Way',      'Cypress Creek','USA',       NOW()),
    (4, 'Initech',           'Bill Lumbergh', 'blumbergh@initech.example', '555-1004', '15 Corporate Dr.',  'Dallas',       'USA',       NOW()),
    (5, 'Umbrella Trading',  'Alice Wong',    'awong@umbrella.example',    '555-1005', '8 Commerce St.',    'Hong Kong',    'China',     NOW());

INSERT INTO products VALUES
    (1, 'Heavy Freight Crate',    1, 'Packaging',   12.50,  150),
    (2, 'Climate Box (Cold)',      1, 'Packaging',   48.00,   42),
    (3, 'Standard Pallet',         2, 'Packaging',    8.75,  300),
    (4, 'Fragile Item Wrap',       2, 'Packaging',    3.20,   87),
    (5, 'Hazmat Container L1',     3, 'Hazmat',     120.00,    8),
    (6, 'Express Courier Label',   1, 'Labeling',     1.50, 1000),
    (7, 'Refrigerated Container',  1, 'Cold Chain', 350.00,    4),
    (8, 'Document Envelope',       2, 'Labeling',     0.75, 2000);

INSERT INTO orders (customer_id, employee_id, order_date, ship_date, status, note) VALUES
    (1, 2, '2024-01-15 09:00:00', '2024-01-18 14:00:00', 'shipped',   'Handle with care, priority client'),
    (2, 2, '2024-01-22 11:30:00', NULL,                   'pending',   NULL),
    (3, 2, '2024-02-01 08:00:00', '2024-02-03 12:00:00', 'shipped',   'Fragile contents'),
    (4, 2, '2024-02-10 14:00:00', NULL,                   'cancelled', 'Customer cancelled — duplicate order'),
    (5, 2, '2024-02-14 10:00:00', NULL,                   'pending',   'Requires customs clearance'),
    (1, 2, '2024-03-01 09:00:00', NULL,                   'pending',   NULL);

INSERT INTO order_items (order_id, product_id, quantity, unit_price) VALUES
    (1, 1, 10,  12.50),
    (1, 6, 100,  1.50),
    (2, 3,  5,   8.75),
    (2, 4, 20,   3.20),
    (3, 2,  2,  48.00),
    (3, 5,  1, 120.00),
    (4, 1,  3,  12.50),
    (5, 7,  1, 350.00),
    (5, 5,  2, 120.00),
    (6, 8, 50,   0.75),
    (6, 6, 200,  1.50);
