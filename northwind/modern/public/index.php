<?php

declare(strict_types=1);

use DI\ContainerBuilder;
use Northwind\Handler\GetOrderHandler;
use Northwind\Handler\ListOrdersHandler;
use Northwind\Repository\OrderRepository;
use Slim\Factory\AppFactory;

require __DIR__ . '/../vendor/autoload.php';

$builder = new ContainerBuilder();
$builder->addDefinitions([
    PDO::class => function (): PDO {
        return new PDO(
            sprintf(
                'mysql:host=%s;dbname=%s;charset=utf8mb4',
                $_ENV['DB_HOST'] ?? 'db',
                $_ENV['DB_NAME'] ?? 'northwind',
            ),
            $_ENV['DB_USER'] ?? 'northwind',
            $_ENV['DB_PASS'] ?? 'northwind123',
            [
                PDO::ATTR_ERRMODE            => PDO::ERRMODE_EXCEPTION,
                PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC,
                PDO::ATTR_EMULATE_PREPARES   => false,
            ],
        );
    },
    OrderRepository::class => DI\autowire(),
]);

$container = $builder->build();
AppFactory::setContainer($container);

$app = AppFactory::create();
$app->addErrorMiddleware(true, true, true);

$app->get('/api/orders',              ListOrdersHandler::class);
$app->get('/api/orders/{id:[0-9]+}',  GetOrderHandler::class);

$app->run();
