<?php

declare(strict_types=1);

namespace Northwind\Repository;

use PDO;

final class OrderRepository
{
    public function __construct(private readonly PDO $db) {}

    /**
     * @return list<array<string, mixed>>
     */
    public function list(string $status = '', int $customerId = 0): array
    {
        $where  = ['1=1'];
        $params = [];

        if ($status !== '') {
            $where[]           = 'o.status = :status';
            $params[':status'] = $status;
        }

        if ($customerId > 0) {
            $where[]       = 'o.customer_id = :cid';
            $params[':cid'] = $customerId;
        }

        $stmt = $this->db->prepare(sprintf(
            "SELECT o.order_id, o.order_date, o.ship_date, o.status,
                    c.company_name, c.customer_id,
                    e.first_name, e.last_name,
                    COUNT(oi.item_id)                              AS item_count,
                    COALESCE(SUM(oi.quantity * oi.unit_price), 0)  AS total
             FROM orders o
             JOIN customers   c  ON o.customer_id = c.customer_id
             JOIN employees   e  ON o.employee_id = e.employee_id
             LEFT JOIN order_items oi ON o.order_id = oi.order_id
             WHERE %s
             GROUP BY o.order_id
             ORDER BY o.order_date DESC
             LIMIT 200",
            implode(' AND ', $where),
        ));

        $stmt->execute($params);
        return $stmt->fetchAll();
    }

    /** @return array<string, mixed>|null */
    public function findById(int $id): ?array
    {
        $stmt = $this->db->prepare(
            "SELECT o.*, c.company_name, c.contact_name, c.email, c.phone,
                    e.first_name, e.last_name
             FROM orders o
             JOIN customers c ON o.customer_id = c.customer_id
             JOIN employees e ON o.employee_id = e.employee_id
             WHERE o.order_id = :id",
        );
        $stmt->execute([':id' => $id]);
        $order = $stmt->fetch() ?: null;

        if ($order === null) {
            return null;
        }

        $stmt = $this->db->prepare(
            "SELECT oi.*, p.product_name
             FROM order_items oi
             JOIN products p ON oi.product_id = p.product_id
             WHERE oi.order_id = :id",
        );
        $stmt->execute([':id' => $id]);
        $order['items'] = $stmt->fetchAll();

        return $order;
    }
}
