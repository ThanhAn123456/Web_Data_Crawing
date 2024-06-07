CREATE DATABASE local_db;
USE local_db;
CREATE TABLE products (
    product_id INT NOT NULL,
    name nvarchar(300) NOT NULL DEFAULT '',
    price float NOT NULL,
    quantity float NOT NULL,
    image nvarchar(300) NOT NULL DEFAULT '',
    PRIMARY KEY (product_id)
);