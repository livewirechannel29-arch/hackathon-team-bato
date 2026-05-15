<?php

declare(strict_types=1);

namespace Northwind\Handler;

use Northwind\Repository\OrderRepository;
use Psr\Http\Message\ResponseInterface;
use Psr\Http\Message\ServerRequestInterface;

final class GetOrderHandler
{
    public function __construct(private readonly OrderRepository $orders) {}

    public function __invoke(
        ServerRequestInterface $request,
        ResponseInterface $response,
        array $args,
    ): ResponseInterface {
        $order = $this->orders->findById((int) $args['id']);

        if ($order === null) {
            $response->getBody()->write(json_encode(['error' => 'Order not found']));
            return $response->withStatus(404)->withHeader('Content-Type', 'application/json');
        }

        $response->getBody()->write(json_encode($order, JSON_THROW_ON_ERROR));
        return $response->withHeader('Content-Type', 'application/json');
    }
}
