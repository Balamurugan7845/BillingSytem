CREATE DATABASE shop_billing;
USE shop_billing;
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL
);

CREATE TABLE customers (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100),
    phone VARCHAR(20),
    email VARCHAR(100),
    address TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE products (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100),
    price DECIMAL(10,2),
    stock INT DEFAULT 0,
    barcode VARCHAR(100)
);

CREATE TABLE bills (
    id INT AUTO_INCREMENT PRIMARY KEY,
    customer_id INT,
    bill_number VARCHAR(50),
    total_amount DECIMAL(10,2),
    discount_type VARCHAR(50),
    discount_value DECIMAL(10,2),
    discount_amount DECIMAL(10,2),
    gst_type VARCHAR(50),
    cgst_amount DECIMAL(10,2),
    sgst_amount DECIMAL(10,2),
    igst_amount DECIMAL(10,2),
    gst_amount DECIMAL(10,2),
    final_amount DECIMAL(10,2),
    payment_method VARCHAR(50),
    upi_id VARCHAR(100),
    card_number VARCHAR(100),
    card_name VARCHAR(100),
    status VARCHAR(50) DEFAULT 'Pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (customer_id) REFERENCES customers(id)
);

CREATE TABLE bill_items (
    id INT AUTO_INCREMENT PRIMARY KEY,
    bill_id INT,
    product_id INT,
    quantity INT,
    unit_price DECIMAL(10,2),
    total_price DECIMAL(10,2),
    FOREIGN KEY (bill_id) REFERENCES bills(id),
    FOREIGN KEY (product_id) REFERENCES products(id)
);