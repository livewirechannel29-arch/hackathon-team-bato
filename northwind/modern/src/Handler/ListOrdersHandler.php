<?php

declare(strict_types=1);

namespace Northwind\Handler;

use Northwind\Repository\OrderRepository;
use Psr\Http\Message\ResponseInterface;
use Psr\Http\Message\ServerRequestInterface;

final class ListOrdersHandler
{
    public function __construct(private readonly OrderRepository $orders) {}

    public function __invoke(
        ServerRequestInterface $request,
        ResponseInterface $response,
    ): ResponseInterface {
        $params     = $request->getQueryParams();
        $status     = (string) ($params['status']      ?? '');
        $customerId = (int)    ($params['customer_id'] ?? 0);

        $orders = $this->orders->list($status, $customerId);

        $response->getBody()->write(json_encode(
            ['data' => $orders, 'count' => count($orders)],
            JSON_THROW_ON_ERROR,
        ));

        return $response->withHeader('Content-Type', 'application/json');
    }
}
