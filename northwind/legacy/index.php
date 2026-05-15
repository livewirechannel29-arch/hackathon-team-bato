<?php
// =============================================================
// Northwind Logistics — Internal Web App  v1.0.3
// Last touched: Steve K., sometime around 2011
// "If it ain't broke don't fix it" — Gary (mgmt, retired 2019)
// =============================================================

session_start();
error_reporting(0); // Gary said to turn this off before go-live

$conn = mysql_connect('db', 'northwind', 'northwind123')
    or die('Cannot connect to database. Call IT at x4400.');
mysql_select_db('northwind', $conn)
    or die('Cannot select database.');

// ---- Login -------------------------------------------------------
if ($_SERVER['REQUEST_METHOD'] === 'POST' && $_POST['action'] == 'login') {
    $username = $_POST['username'];   // TODO: sanitize someday
    $password = $_POST['password'];

    $sql = "SELECT * FROM employees WHERE username = '$username' AND password = '$password' AND active = 1";
    $result = mysql_query($sql, $conn);

    if ($result && mysql_num_rows($result) > 0) {
        $emp = mysql_fetch_assoc($result);
        $_SESSION['uid']   = $emp['employee_id'];
        $_SESSION['uname'] = $emp['first_name'] . ' ' . $emp['last_name'];
        $_SESSION['role']  = $emp['role'];
        header('Location: index.php?page=orders');
        exit;
    } else {
        $login_error = 'Bad username or password.';
    }
}

if (isset($_GET['logout'])) {
    session_destroy();
    header('Location: index.php?page=login');
    exit;
}

// ---- Route -------------------------------------------------------
$page = isset($_GET['page']) ? $_GET['page'] : 'orders';

if ($page != 'login' && empty($_SESSION['uid'])) {
    header('Location: index.php?page=login');
    exit;
}

// ---- Mutations (POST) --------------------------------------------
if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    if (isset($_POST['action'])) {

        if ($_POST['action'] == 'ship_order') {
            $order_id = intval($_POST['order_id']); // at least Gary remembered to cast this one
            $sql = "UPDATE orders SET status = 'shipped', ship_date = NOW() WHERE order_id = $order_id";
            mysql_query($sql, $conn);
            header("Location: index.php?page=order_detail&id=$order_id&msg=shipped");
            exit;
        }

        if ($_POST['action'] == 'add_order') {
            $cid  = $_POST['customer_id'];
            $note = $_POST['note'];  // not escaped — Steve trusted internal users
            $sql  = "INSERT INTO orders (customer_id, employee_id, order_date, status, note)
                     VALUES ('$cid', '" . $_SESSION['uid'] . "', NOW(), 'pending', '$note')";
            mysql_query($sql, $conn);
            $new_id = mysql_insert_id($conn);
            header("Location: index.php?page=order_detail&id=$new_id");
            exit;
        }

        if ($_POST['action'] == 'update_customer') {
            $cid   = intval($_POST['customer_id']);
            $email = $_POST['email'];
            $phone = $_POST['phone'];
            $sql   = "UPDATE customers SET email='$email', phone='$phone' WHERE customer_id=$cid";
            mysql_query($sql, $conn);
            header('Location: index.php?page=customers&msg=saved');
            exit;
        }

    }
}

// ---- HTML header -------------------------------------------------
?><!DOCTYPE html>
<html>
<head>
    <title>Northwind Logistics</title>
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
</head>
<body>
<?php if ($page != 'login'): ?>
<div id="hdr">
    <strong>Northwind Logistics</strong> &nbsp;|&nbsp;
    <a href="index.php?page=orders">Orders</a>
    <a href="index.php?page=customers">Customers</a>
    <a href="index.php?page=products">Products</a>
    <?php if ($_SESSION['role'] == 'admin'): ?>
        <a href="index.php?page=reports">Reports</a>
    <?php endif; ?>
    &nbsp;&nbsp; logged in as <strong><?= $_SESSION['uname'] ?></strong>
    &nbsp; <a href="index.php?logout=1">Logout</a>
</div>
<?php endif; ?>
<div id="wrap">
<?php if (isset($_GET['msg']) && $_GET['msg'] == 'shipped'): ?>
    <div class="msg">Order marked as shipped.</div>
<?php endif; ?>
<?php if (isset($_GET['msg']) && $_GET['msg'] == 'saved'): ?>
    <div class="msg">Customer saved.</div>
<?php endif; ?>

<?php
// =========================================================
// PAGE: login
// =========================================================
if ($page == 'login'):
?>
    <h2>Northwind Logistics — Sign In</h2>
    <?php if (!empty($login_error)): ?><div class="err"><?= $login_error ?></div><?php endif; ?>
    <form method="post" action="index.php">
        <input type="hidden" name="action" value="login">
        <table style="width:300px">
            <tr><td>Username</td><td><input name="username" type="text" style="width:160px"></td></tr>
            <tr><td>Password</td><td><input name="password" type="password" style="width:160px"></td></tr>
            <tr><td colspan="2" style="padding-top:8px"><button class="btn" type="submit">Login</button></td></tr>
        </table>
    </form>

<?php
// =========================================================
// PAGE: orders list
// =========================================================
elseif ($page == 'orders'):
    $filter_status = isset($_GET['status'])      ? $_GET['status']           : '';
    $filter_cid    = isset($_GET['customer_id']) ? intval($_GET['customer_id']) : 0;

    $sql = "SELECT o.order_id, o.order_date, o.ship_date, o.status,
                   c.company_name, c.customer_id,
                   e.first_name, e.last_name,
                   COUNT(oi.item_id) AS item_count,
                   COALESCE(SUM(oi.quantity * oi.unit_price), 0) AS total
            FROM orders o
            JOIN customers c    ON o.customer_id = c.customer_id
            JOIN employees e    ON o.employee_id = e.employee_id
            LEFT JOIN order_items oi ON o.order_id = oi.order_id
            WHERE 1=1";

    if ($filter_status) {
        $filter_status = mysql_real_escape_string($filter_status, $conn); // rare moment of caution
        $sql .= " AND o.status = '$filter_status'";
    }
    if ($filter_cid) {
        $sql .= " AND o.customer_id = $filter_cid";
    }

    $sql .= " GROUP BY o.order_id ORDER BY o.order_date DESC LIMIT 200";
    $result = mysql_query($sql, $conn);
?>
    <h2>Orders</h2>
    <p>
        Filter:
        <a href="?page=orders">All</a> |
        <a href="?page=orders&status=pending">Pending</a> |
        <a href="?page=orders&status=shipped">Shipped</a> |
        <a href="?page=orders&status=cancelled">Cancelled</a>
    </p>
    <table>
        <tr>
            <th>#</th><th>Customer</th><th>Handler</th>
            <th>Order Date</th><th>Ship Date</th>
            <th>Items</th><th>Total</th><th>Status</th><th></th>
        </tr>
        <?php while ($row = mysql_fetch_assoc($result)): ?>
        <tr>
            <td><?= $row['order_id'] ?></td>
            <td><a href="?page=customers&id=<?= $row['customer_id'] ?>"><?= htmlspecialchars($row['company_name']) ?></a></td>
            <td><?= htmlspecialchars($row['first_name'] . ' ' . $row['last_name']) ?></td>
            <td><?= $row['order_date'] ?></td>
            <td><?= $row['ship_date'] ? $row['ship_date'] : '—' ?></td>
            <td><?= $row['item_count'] ?></td>
            <td>$<?= number_format($row['total'], 2) ?></td>
            <td><span class="status-<?= $row['status'] ?>"><?= ucfirst($row['status']) ?></span></td>
            <td><a href="?page=order_detail&id=<?= $row['order_id'] ?>">View</a></td>
        </tr>
        <?php endwhile; ?>
    </table>

<?php
// =========================================================
// PAGE: order detail
// =========================================================
elseif ($page == 'order_detail'):
    $oid = intval($_GET['id']);
    $sql = "SELECT o.*, c.company_name, c.contact_name, c.email, c.phone,
                   e.first_name, e.last_name
            FROM orders o
            JOIN customers c ON o.customer_id = c.customer_id
            JOIN employees e ON o.employee_id = e.employee_id
            WHERE o.order_id = $oid";
    $result = mysql_query($sql, $conn);
    $order  = mysql_fetch_assoc($result);

    $sql_items = "SELECT oi.*, p.product_name
                  FROM order_items oi
                  JOIN products p ON oi.product_id = p.product_id
                  WHERE oi.order_id = $oid";
    $items = mysql_query($sql_items, $conn);
?>
    <h2>Order #<?= $oid ?></h2>
    <table style="width:500px;margin-bottom:16px">
        <tr><th colspan="2">Order Info</th></tr>
        <tr><td>Customer</td>  <td><?= htmlspecialchars($order['company_name']) ?> (<?= htmlspecialchars($order['contact_name']) ?>)</td></tr>
        <tr><td>Email</td>     <td><?= htmlspecialchars($order['email']) ?></td></tr>
        <tr><td>Phone</td>     <td><?= htmlspecialchars($order['phone']) ?></td></tr>
        <tr><td>Handler</td>   <td><?= htmlspecialchars($order['first_name'] . ' ' . $order['last_name']) ?></td></tr>
        <tr><td>Order Date</td><td><?= $order['order_date'] ?></td></tr>
        <tr><td>Ship Date</td> <td><?= $order['ship_date'] ? $order['ship_date'] : 'Not shipped' ?></td></tr>
        <tr><td>Status</td>    <td><span class="status-<?= $order['status'] ?>"><?= ucfirst($order['status']) ?></span></td></tr>
        <tr><td>Note</td>      <td><?= htmlspecialchars($order['note']) ?></td></tr>
    </table>

    <h3>Line Items</h3>
    <table>
        <tr><th>Product</th><th>Qty</th><th>Unit Price</th><th>Subtotal</th></tr>
        <?php $grand = 0; while ($item = mysql_fetch_assoc($items)):
              $sub = $item['quantity'] * $item['unit_price'];
              $grand += $sub;
        ?>
        <tr>
            <td><?= htmlspecialchars($item['product_name']) ?></td>
            <td><?= $item['quantity'] ?></td>
            <td>$<?= number_format($item['unit_price'], 2) ?></td>
            <td>$<?= number_format($sub, 2) ?></td>
        </tr>
        <?php endwhile; ?>
        <tr>
            <td colspan="3"><strong>Total</strong></td>
            <td><strong>$<?= number_format($grand, 2) ?></strong></td>
        </tr>
    </table>

    <?php if ($order['status'] == 'pending' && $_SESSION['role'] != 'viewer'): ?>
    <p>
        <form method="post" action="index.php" style="display:inline">
            <input type="hidden" name="action"   value="ship_order">
            <input type="hidden" name="order_id" value="<?= $oid ?>">
            <button class="btn" type="submit">Mark as Shipped</button>
        </form>
    </p>
    <?php endif; ?>
    <p><a href="?page=orders">← Back to Orders</a></p>

<?php
// =========================================================
// PAGE: customers
// =========================================================
elseif ($page == 'customers'):
    if (isset($_GET['id'])) {
        $cid = intval($_GET['id']);
        $sql = "SELECT * FROM customers WHERE customer_id = $cid";
        $result = mysql_query($sql, $conn);
        $cust   = mysql_fetch_assoc($result);

        // correlated subquery — Steve was proud of this one
        $sql_orders = "SELECT order_id, order_date, status,
                              (SELECT COALESCE(SUM(quantity*unit_price),0) FROM order_items WHERE order_id=o.order_id) AS total
                       FROM orders o
                       WHERE customer_id = $cid
                       ORDER BY order_date DESC";
        $ords = mysql_query($sql_orders, $conn);
?>
        <h2>Customer: <?= htmlspecialchars($cust['company_name']) ?></h2>
        <form method="post" action="index.php">
            <input type="hidden" name="action"      value="update_customer">
            <input type="hidden" name="customer_id" value="<?= $cust['customer_id'] ?>">
            <table style="width:420px;margin-bottom:16px">
                <tr><td>Contact</td><td><?= htmlspecialchars($cust['contact_name']) ?></td></tr>
                <tr><td>Email</td>
                    <td><input type="text" name="email" value="<?= htmlspecialchars($cust['email']) ?>" style="width:220px"></td></tr>
                <tr><td>Phone</td>
                    <td><input type="text" name="phone" value="<?= htmlspecialchars($cust['phone']) ?>" style="width:140px"></td></tr>
                <tr><td>Address</td>
                    <td><?= htmlspecialchars($cust['address'] . ', ' . $cust['city'] . ', ' . $cust['country']) ?></td></tr>
                <tr><td colspan="2" style="padding-top:8px">
                    <button class="btn" type="submit">Save</button>
                </td></tr>
            </table>
        </form>
        <h3>Order History</h3>
        <table>
            <tr><th>#</th><th>Date</th><th>Status</th><th>Total</th><th></th></tr>
            <?php while ($o = mysql_fetch_assoc($ords)): ?>
            <tr>
                <td><?= $o['order_id'] ?></td>
                <td><?= $o['order_date'] ?></td>
                <td><span class="status-<?= $o['status'] ?>"><?= ucfirst($o['status']) ?></span></td>
                <td>$<?= number_format($o['total'], 2) ?></td>
                <td><a href="?page=order_detail&id=<?= $o['order_id'] ?>">View</a></td>
            </tr>
            <?php endwhile; ?>
        </table>
        <p><a href="?page=customers">← All Customers</a></p>
<?php
    } else {
        $sql = "SELECT c.*, COUNT(o.order_id) AS order_count
                FROM customers c
                LEFT JOIN orders o ON c.customer_id = o.customer_id
                GROUP BY c.customer_id
                ORDER BY c.company_name";
        $result = mysql_query($sql, $conn);
?>
        <h2>Customers</h2>
        <table>
            <tr><th>Company</th><th>Contact</th><th>City</th><th>Country</th><th>Orders</th><th></th></tr>
            <?php while ($row = mysql_fetch_assoc($result)): ?>
            <tr>
                <td><?= htmlspecialchars($row['company_name']) ?></td>
                <td><?= htmlspecialchars($row['contact_name']) ?></td>
                <td><?= htmlspecialchars($row['city']) ?></td>
                <td><?= htmlspecialchars($row['country']) ?></td>
                <td><?= $row['order_count'] ?></td>
                <td><a href="?page=customers&id=<?= $row['customer_id'] ?>">Edit</a></td>
            </tr>
            <?php endwhile; ?>
        </table>
<?php
    }

// =========================================================
// PAGE: products
// =========================================================
elseif ($page == 'products'):
    $sql = "SELECT p.*, s.company_name AS supplier_name
            FROM products p
            JOIN suppliers s ON p.supplier_id = s.supplier_id
            ORDER BY p.product_name";
    $result = mysql_query($sql, $conn);
?>
    <h2>Products</h2>
    <table>
        <tr><th>Product</th><th>Category</th><th>Supplier</th><th>Price</th><th>In Stock</th></tr>
        <?php while ($row = mysql_fetch_assoc($result)): ?>
        <tr>
            <td><?= htmlspecialchars($row['product_name']) ?></td>
            <td><?= htmlspecialchars($row['category']) ?></td>
            <td><?= htmlspecialchars($row['supplier_name']) ?></td>
            <td>$<?= number_format($row['unit_price'], 2) ?></td>
            <td><?php
                if ($row['units_in_stock'] <= 10) {
                    echo '<strong style="color:red">' . $row['units_in_stock'] . ' LOW</strong>';
                } else {
                    echo $row['units_in_stock'];
                }
            ?></td>
        </tr>
        <?php endwhile; ?>
    </table>

<?php
// =========================================================
// PAGE: reports (admin only)
// =========================================================
elseif ($page == 'reports'):
    if ($_SESSION['role'] != 'admin') {
        echo '<p class="err">Access denied.</p>';
    } else {
        $sql = "SELECT DATE_FORMAT(o.order_date, '%Y-%m') AS month,
                       COUNT(DISTINCT o.order_id)           AS orders,
                       COALESCE(SUM(oi.quantity * oi.unit_price), 0) AS revenue
                FROM orders o
                LEFT JOIN order_items oi ON o.order_id = oi.order_id
                WHERE o.status != 'cancelled'
                GROUP BY month
                ORDER BY month DESC
                LIMIT 24";
        $result = mysql_query($sql, $conn);
?>
    <h2>Monthly Revenue</h2>
    <table style="width:360px">
        <tr><th>Month</th><th>Orders</th><th>Revenue</th></tr>
        <?php while ($row = mysql_fetch_assoc($result)): ?>
        <tr>
            <td><?= $row['month'] ?></td>
            <td><?= $row['orders'] ?></td>
            <td>$<?= number_format($row['revenue'], 2) ?></td>
        </tr>
        <?php endwhile; ?>
    </table>
<?php
    }

endif; // end page routing
?>
</div><!-- /wrap -->
</body>
</html>
