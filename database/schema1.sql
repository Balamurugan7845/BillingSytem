-- Create Database
CREATE DATABASE IF NOT EXISTS shop_billing_system;
USE shop_billing_system;

-- Users table for admin authentication
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Products table
CREATE TABLE products (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    price DECIMAL(10,2) NOT NULL,
    stock INT NOT NULL DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Customers table
CREATE TABLE customers (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    phone VARCHAR(15),
    email VARCHAR(100),
    address TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Bills table (Enhanced with discount and GST fields)
CREATE TABLE bills (
    id INT AUTO_INCREMENT PRIMARY KEY,
    customer_id INT,
    bill_number VARCHAR(20) UNIQUE NOT NULL,
    total_amount DECIMAL(10,2) NOT NULL,  -- Subtotal before discount
    discount_type VARCHAR(20) DEFAULT 'none',
    discount_value DECIMAL(10,2) DEFAULT 0,
    discount_amount DECIMAL(10,2) DEFAULT 0,
    taxable_amount DECIMAL(10,2) DEFAULT 0,  -- After discount
    gst_type VARCHAR(20) DEFAULT 'cgst_sgst',
    cgst_amount DECIMAL(10,2) DEFAULT 0,
    sgst_amount DECIMAL(10,2) DEFAULT 0,
    igst_amount DECIMAL(10,2) DEFAULT 0,
    gst_amount DECIMAL(10,2) NOT NULL,  -- Total GST
    final_amount DECIMAL(10,2) NOT NULL,  -- Final total after discount and GST
    payment_method VARCHAR(20) DEFAULT 'Cash',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE SET NULL
);

-- Bill items table
CREATE TABLE bill_items (
    id INT AUTO_INCREMENT PRIMARY KEY,
    bill_id INT NOT NULL,
    product_id INT NOT NULL,
    quantity INT NOT NULL,
    unit_price DECIMAL(10,2) NOT NULL,
    total_price DECIMAL(10,2) NOT NULL,
    FOREIGN KEY (bill_id) REFERENCES bills(id) ON DELETE CASCADE,
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
);

-- Insert sample products
INSERT INTO products (name, price, stock) VALUES
('Laptop', 45000.00, 10),
('Mouse', 500.00, 50),
('Keyboard', 1200.00, 30),
('Monitor', 8000.00, 15),
('Headphones', 1500.00, 25),
('USB Cable', 200.00, 100),
('Webcam', 2500.00, 20),
('Speaker', 3000.00, 12);

-- Insert sample customers (Updated as requested)
INSERT INTO customers (name, phone, email, address) VALUES 
('Makesh', '8903309347', 'makesh@email.com', 'kaveri street ,kumbakonam'),
('Shafeer', '9597130526', 'mdshafeer0205@gmail.com', '131 Railway Station Road , Ammapettai,Thanjavur'),
('Arun', '9751753807', 'arun@email.com', '172 TB Santorium,vennampatti'),
('Sri Baran', '6381372224', 'Sribaran@email.com', '321 south Street, puddukotai'),
('Manirathanam', '9342931218', 'manirathnam@email.com', '654 south street, vendayampatti');

INSERT INTO bills 
(customer_id, payment_method, discount_type, discount_value, gst_type, subtotal, 
 discount_amount, cgst, sgst, igst, final_total)
VALUES
(1, 'Cash', 'none', 0, 'cgst_sgst', 10000.00, 0.00, 900.00, 900.00, 0.00, 11800.00),
(2, 'UPI', 'percent', 10, 'cgst_sgst', 5000.00, 500.00, 405.00, 405.00, 0.00, 5310.00),
(3, 'Card', 'flat', 200, 'cgst_sgst', 8000.00, 200.00, 702.00, 702.00, 0.00, 9204.00),
(4, 'Cash', 'none', 0, 'igst', 4000.00, 0.00, 0.00, 0.00, 720.00, 4720.00);


-- Add new columns to bills table if it already exists
ALTER TABLE bills 
ADD COLUMN IF NOT EXISTS discount_type VARCHAR(20) DEFAULT 'none',
ADD COLUMN IF NOT EXISTS discount_value DECIMAL(10,2) DEFAULT 0,
ADD COLUMN IF NOT EXISTS discount_amount DECIMAL(10,2) DEFAULT 0,
ADD COLUMN IF NOT EXISTS taxable_amount DECIMAL(10,2) DEFAULT 0,
ADD COLUMN IF NOT EXISTS gst_type VARCHAR(20) DEFAULT 'cgst_sgst',
ADD COLUMN IF NOT EXISTS cgst_amount DECIMAL(10,2) DEFAULT 0,
ADD COLUMN IF NOT EXISTS sgst_amount DECIMAL(10,2) DEFAULT 0,
ADD COLUMN IF NOT EXISTS igst_amount DECIMAL(10,2) DEFAULT 0;

-- Update existing bills to have default values
UPDATE bills SET 
    discount_type = 'none',
    discount_value = 0,
    discount_amount = 0,
    taxable_amount = total_amount,
    gst_type = 'cgst_sgst',
    cgst_amount = gst_amount / 2,
    sgst_amount = gst_amount / 2,
    igst_amount = 0
WHERE discount_type IS NULL;

-- View all bills with customer information
SELECT 
    b.id,
    b.bill_number,
    c.name as customer_name,
    b.total_amount as subtotal,
    b.discount_amount,
    b.taxable_amount,
    b.gst_amount,
    b.final_amount,
    b.payment_method,
    b.created_at
FROM bills b
LEFT JOIN customers c ON b.customer_id = c.id
ORDER BY b.created_at DESC;

-- View bill items with product details
SELECT 
    bi.bill_id,
    p.name as product_name,
    bi.quantity,
    bi.unit_price,
    bi.total_price
FROM bill_items bi
JOIN products p ON bi.product_id = p.id
WHERE bi.bill_id = 1;  -- Replace with actual bill ID

-- Daily sales report
SELECT 
    DATE(created_at) as sale_date,
    COUNT(*) as total_bills,
    SUM(final_amount) as total_sales,
    AVG(final_amount) as average_bill_amount
FROM bills
GROUP BY DATE(created_at)
ORDER BY sale_date DESC;

-- Monthly sales summary
SELECT 
    YEAR(created_at) as year,
    MONTH(created_at) as month,
    COUNT(*) as total_bills,
    SUM(final_amount) as total_sales
FROM bills
GROUP BY YEAR(created_at), MONTH(created_at)
ORDER BY year DESC, month DESC;

-- Product sales performance
SELECT 
    p.name as product_name,
    SUM(bi.quantity) as total_sold,
    SUM(bi.total_price) as total_revenue,
    p.stock as current_stock
FROM bill_items bi
JOIN products p ON bi.product_id = p.id
GROUP BY p.id, p.name, p.stock
ORDER BY total_sold DESC;

-- Customer purchase history
SELECT 
    c.name as customer_name,
    COUNT(b.id) as total_bills,
    SUM(b.final_amount) as total_spent,
    AVG(b.final_amount) as average_bill_amount
FROM customers c
LEFT JOIN bills b ON c.id = b.customer_id
GROUP BY c.id, c.name
ORDER BY total_spent DESC;

-- Reset auto-increment counters (if needed)
ALTER TABLE users AUTO_INCREMENT = 1;
ALTER TABLE products AUTO_INCREMENT = 1;
ALTER TABLE customers AUTO_INCREMENT = 1;
ALTER TABLE bills AUTO_INCREMENT = 1;
ALTER TABLE bill_items AUTO_INCREMENT = 1;

-- Backup query (create a copy of important tables)
CREATE TABLE bills_backup AS SELECT * FROM bills;
CREATE TABLE bill_items_backup AS SELECT * FROM bill_items;
CREATE TABLE products_backup AS SELECT * FROM products;
CREATE TABLE customers_backup AS SELECT * FROM customers;

-- Check database size
SELECT 
    table_name AS `Table`,
    ROUND(((data_length + index_length) / 1024 / 1024), 2) AS `Size (MB)`
FROM information_schema.TABLES
WHERE table_schema = 'shop_billing_system'
ORDER BY (data_length + index_length) DESC;





-- Create indexes for better performance
CREATE INDEX idx_bills_date ON bills(created_at);
CREATE INDEX idx_bills_customer ON bills(customer_id);
CREATE INDEX idx_products_name ON products(name);
CREATE INDEX idx_customers_name ON customers(name);
CREATE INDEX idx_bill_items_bill ON bill_items(bill_id);
CREATE INDEX idx_bill_items_product ON bill_items(product_id);

-- Create views for reporting
CREATE VIEW daily_sales AS
SELECT 
    DATE(created_at) as sale_date,
    COUNT(*) as total_bills,
    SUM(final_amount) as total_sales
FROM bills 
GROUP BY DATE(created_at);

CREATE VIEW product_sales AS
SELECT 
    p.id,
    p.name,
    SUM(bi.quantity) as total_sold,
    SUM(bi.total) as total_revenue
FROM products p
LEFT JOIN bill_items bi ON p.id = bi.product_id
GROUP BY p.id, p.name;

-- Show table structure verification
SELECT 'Database setup completed successfully!' as status;


ALTER TABLE bills 
ADD COLUMN subtotal DECIMAL(10,2) DEFAULT 0,
ADD COLUMN discount_amount DECIMAL(10,2) DEFAULT 0,
ADD COLUMN gst_type VARCHAR(20) DEFAULT 'cgst_sgst',
ADD COLUMN cgst DECIMAL(10,2) DEFAULT 0,
ADD COLUMN sgst DECIMAL(10,2) DEFAULT 0,
ADD COLUMN igst DECIMAL(10,2) DEFAULT 0;


DROP TABLE IF EXISTS bills;
CREATE TABLE IF NOT EXISTS bills (
    id INT AUTO_INCREMENT PRIMARY KEY,
    customer_id INT NULL,
    payment_method VARCHAR(20),

    discount_type VARCHAR(20),
    discount_value DECIMAL(10,2),

    gst_type VARCHAR(20),

    subtotal DECIMAL(10,2),
    discount_amount DECIMAL(10,2),

    cgst DECIMAL(10,2),
    sgst DECIMAL(10,2),
    igst DECIMAL(10,2),

    final_total DECIMAL(10,2),

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE SET NULL
);

USE your_database_name;
SHOW TABLES;
DESCRIBE bills;
DROP TABLE bills;


SET FOREIGN_KEY_CHECKS = 0;
DROP TABLE bill_items;
DROP TABLE bills;
CREATE TABLE bills (
    id INT AUTO_INCREMENT PRIMARY KEY,
    customer_id INT NULL,
    payment_method VARCHAR(20),

    discount_type VARCHAR(20),
    discount_value DECIMAL(10,2),

    gst_type VARCHAR(20),

    subtotal DECIMAL(10,2),
    discount_amount DECIMAL(10,2),

    cgst DECIMAL(10,2),
    sgst DECIMAL(10,2),
    igst DECIMAL(10,2),

    final_total DECIMAL(10,2),

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE SET NULL
);
CREATE TABLE bill_items (
    id INT AUTO_INCREMENT PRIMARY KEY,
    bill_id INT,
    product_id INT,
    product_name VARCHAR(255),
    price DECIMAL(10,2),
    qty INT NOT NULL,
    total DECIMAL(10,2),
    FOREIGN KEY (bill_id) REFERENCES bills(id) ON DELETE CASCADE,
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
);

ALTER TABLE bills 
ADD COLUMN upi_id VARCHAR(50) DEFAULT NULL,
ADD COLUMN card_number VARCHAR(20) DEFAULT NULL,
ADD COLUMN card_name VARCHAR(100) DEFAULT NULL;
