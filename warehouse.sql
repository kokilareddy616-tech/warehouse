-- ============================================================
-- Smart Inventory & Warehouse Tracker - Database Schema
-- ============================================================

CREATE DATABASE IF NOT EXISTS warehouse_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE warehouse_db;

-- ============================================================
-- TABLE: users
-- ============================================================
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    role ENUM('admin', 'manager', 'staff') DEFAULT 'staff',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO users (username, password, role) VALUES
('admin', 'admin123', 'admin'),
('manager', 'manager123', 'manager'),
('staff1', 'staff123', 'staff');

-- ============================================================
-- TABLE: warehouse
-- ============================================================
CREATE TABLE IF NOT EXISTS warehouse (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    location VARCHAR(200) NOT NULL,
    city VARCHAR(100) NOT NULL,
    state VARCHAR(100) NOT NULL,
    capacity INT NOT NULL COMMENT 'Max units',
    manager_name VARCHAR(100),
    contact_phone VARCHAR(20),
    status ENUM('active', 'inactive', 'maintenance') DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO warehouse (name, location, city, state, capacity, manager_name, contact_phone, status) VALUES
('Central Hub WH-1', '14 Industrial Estate, Sector 5', 'Mumbai', 'Maharashtra', 50000, 'Rajesh Kumar', '+91-9876543210', 'active'),
('North Delhi WH-2', 'Plot 22, Wazirpur Industrial Area', 'Delhi', 'Delhi', 35000, 'Priya Sharma', '+91-9812345678', 'active'),
('Bengaluru Tech WH-3', '88 Electronic City Phase 2', 'Bengaluru', 'Karnataka', 42000, 'Anand Rao', '+91-9900112233', 'active'),
('Chennai South WH-4', '5 SIPCOT Industrial Park', 'Chennai', 'Tamil Nadu', 28000, 'Kavitha Devi', '+91-9445566778', 'active'),
('Hyderabad WH-5', '101 Nacharam Industrial Area', 'Hyderabad', 'Telangana', 38000, 'Suresh Reddy', '+91-9811223344', 'active'),
('Pune West WH-6', '67 Bhosari MIDC', 'Pune', 'Maharashtra', 22000, 'Meena Joshi', '+91-9765432100', 'maintenance'),
('Ahmedabad WH-7', '33 Naroda Industrial Estate', 'Ahmedabad', 'Gujarat', 30000, 'Dipak Patel', '+91-9898012345', 'active');

-- ============================================================
-- TABLE: supplier
-- ============================================================
CREATE TABLE IF NOT EXISTS supplier (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    contact_person VARCHAR(100),
    email VARCHAR(150) UNIQUE,
    phone VARCHAR(20),
    address TEXT,
    city VARCHAR(100),
    country VARCHAR(100) DEFAULT 'India',
    rating DECIMAL(3,1) DEFAULT 4.0 COMMENT '1.0 to 5.0',
    status ENUM('active', 'inactive', 'blacklisted') DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO supplier (name, contact_person, email, phone, address, city, rating, status) VALUES
('TechParts India Pvt Ltd', 'Amit Verma', 'amit@techparts.in', '+91-9900001111', '12 Okhla Phase 3', 'Delhi', 4.8, 'active'),
('Global Electronics Supply', 'Sara Thomas', 'sara@globalelec.com', '+91-9922334455', '55 Anna Salai', 'Chennai', 4.5, 'active'),
('FastStock Distributors', 'Ravi Nair', 'ravi@faststock.in', '+91-9833445566', '7 MG Road', 'Kochi', 4.2, 'active'),
('Prime Goods Wholesale', 'Neha Singh', 'neha@primegoods.in', '+91-9711223344', '8 Commercial Street', 'Bengaluru', 4.6, 'active'),
('Reliable Parts Co', 'Farhan Khan', 'farhan@reliableparts.in', '+91-9855667788', '22 MIDC Road', 'Pune', 3.9, 'active'),
('Sunrise Traders', 'Jyoti Mehta', 'jyoti@sunrise.in', '+91-9744556677', '100 Ashram Road', 'Ahmedabad', 4.1, 'active'),
('Eastern Supplies Ltd', 'Bikash Das', 'bikash@eastern.in', '+91-9666778899', '45 Park Street', 'Kolkata', 3.7, 'inactive'),
('HyperStock Solutions', 'Pooja Agarwal', 'pooja@hyperstock.in', '+91-9977889900', '33 Sector 18', 'Noida', 4.7, 'active');

-- ============================================================
-- TABLE: employee
-- ============================================================
CREATE TABLE IF NOT EXISTS employee (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(150) UNIQUE,
    phone VARCHAR(20),
    role VARCHAR(100) NOT NULL,
    warehouse_id INT,
    salary DECIMAL(10,2),
    join_date DATE,
    status ENUM('active', 'inactive', 'on_leave') DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (warehouse_id) REFERENCES warehouse(id) ON DELETE SET NULL
);

INSERT INTO employee (name, email, phone, role, warehouse_id, salary, join_date, status) VALUES
('Rajesh Kumar', 'rajesh@warehouse.in', '+91-9876543210', 'Warehouse Manager', 1, 75000.00, '2019-03-15', 'active'),
('Priya Sharma', 'priya@warehouse.in', '+91-9812345678', 'Warehouse Manager', 2, 72000.00, '2020-06-01', 'active'),
('Anand Rao', 'anand@warehouse.in', '+91-9900112233', 'Warehouse Manager', 3, 70000.00, '2020-09-10', 'active'),
('Suresh Reddy', 'suresh@warehouse.in', '+91-9811223344', 'Operations Head', 5, 80000.00, '2018-11-20', 'active'),
('Meena Joshi', 'meena@warehouse.in', '+91-9765432100', 'Stock Supervisor', 6, 55000.00, '2021-01-05', 'on_leave'),
('Arjun Pillai', 'arjun@warehouse.in', '+91-9733445566', 'Logistics Coordinator', 1, 48000.00, '2022-03-22', 'active'),
('Sunita Bose', 'sunita@warehouse.in', '+91-9866778899', 'Inventory Analyst', 3, 52000.00, '2021-07-14', 'active'),
('Kiran Patil', 'kiran@warehouse.in', '+91-9755667788', 'Forklift Operator', 4, 35000.00, '2022-10-01', 'active'),
('Deepak Gupta', 'deepak@warehouse.in', '+91-9644556677', 'Dispatch Clerk', 2, 32000.00, '2023-01-15', 'active'),
('Lalitha Nair', 'lalitha@warehouse.in', '+91-9533445566', 'Quality Inspector', 5, 45000.00, '2022-05-30', 'active');

-- ============================================================
-- TABLE: product
-- ============================================================
CREATE TABLE IF NOT EXISTS product (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(150) NOT NULL,
    sku VARCHAR(50) UNIQUE NOT NULL,
    category VARCHAR(100),
    description TEXT,
    unit_price DECIMAL(12,2) NOT NULL,
    unit VARCHAR(20) DEFAULT 'piece',
    reorder_level INT DEFAULT 50 COMMENT 'Trigger low stock alert if stock <= this',
    supplier_id INT,
    status ENUM('active', 'discontinued', 'pending') DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (supplier_id) REFERENCES supplier(id) ON DELETE SET NULL
);

INSERT INTO product (name, sku, category, description, unit_price, unit, reorder_level, supplier_id, status) VALUES
('Industrial CCTV Camera', 'CCTV-4K-001', 'Electronics', '4K resolution IP security camera with night vision', 8500.00, 'piece', 20, 1, 'active'),
('Barcode Scanner Pro', 'SCAN-BT-002', 'Electronics', 'Bluetooth wireless barcode scanner', 4200.00, 'piece', 30, 2, 'active'),
('Heavy Duty Pallet Wrap', 'WRAP-HD-003', 'Packaging', '500m stretch film roll for pallets', 850.00, 'roll', 100, 3, 'active'),
('Forklift Battery 48V', 'BATT-48V-004', 'Equipment', 'Industrial forklift battery 48V 750Ah', 45000.00, 'piece', 5, 1, 'active'),
('Safety Helmet (Yellow)', 'SAFE-HLM-005', 'Safety', 'ANSI Z89.1 certified industrial safety helmet', 650.00, 'piece', 80, 4, 'active'),
('Thermal Label Printer', 'PRINT-TH-006', 'Electronics', 'Direct thermal label printer 300dpi', 12000.00, 'piece', 15, 2, 'active'),
('Steel Shelving Unit 5-Tier', 'SHELF-ST-007', 'Furniture', 'Heavy duty steel shelving 180x90x40cm', 6800.00, 'piece', 10, 5, 'active'),
('Bubble Wrap Roll 100m', 'WRAP-BB-008', 'Packaging', 'Anti-static bubble wrap for electronics', 520.00, 'roll', 150, 3, 'active'),
('Hydraulic Hand Pallet Jack', 'JACK-HP-009', 'Equipment', '2.5 ton capacity hydraulic pallet truck', 18500.00, 'piece', 8, 6, 'active'),
('High-Vis Safety Vest', 'SAFE-VST-010', 'Safety', 'Fluorescent yellow reflective safety vest', 220.00, 'piece', 200, 4, 'active'),
('Wireless Temperature Logger', 'TEMP-WL-011', 'Electronics', 'IoT temperature and humidity data logger', 3200.00, 'piece', 25, 8, 'active'),
('Corrugated Box 12x10x8', 'BOX-CRG-012', 'Packaging', 'Standard corrugated shipping box', 45.00, 'piece', 500, 3, 'active');

-- ============================================================
-- TABLE: stock
-- ============================================================
CREATE TABLE IF NOT EXISTS stock (
    id INT AUTO_INCREMENT PRIMARY KEY,
    product_id INT NOT NULL,
    warehouse_id INT NOT NULL,
    quantity INT NOT NULL DEFAULT 0,
    last_restocked TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    restocked_by INT,
    notes TEXT,
    FOREIGN KEY (product_id) REFERENCES product(id) ON DELETE CASCADE,
    FOREIGN KEY (warehouse_id) REFERENCES warehouse(id) ON DELETE CASCADE,
    FOREIGN KEY (restocked_by) REFERENCES employee(id) ON DELETE SET NULL,
    UNIQUE KEY unique_product_warehouse (product_id, warehouse_id)
);

INSERT INTO stock (product_id, warehouse_id, quantity, last_restocked, restocked_by, notes) VALUES
(1, 1, 145, '2024-12-10 09:00:00', 1, 'Regular restock from TechParts'),
(1, 3, 88, '2024-12-08 14:00:00', 3, 'Transferred from Mumbai'),
(2, 1, 12, '2024-11-25 10:30:00', 1, 'Low stock - urgent restock needed'),
(2, 2, 67, '2024-12-05 11:00:00', 2, 'Bulk order received'),
(3, 1, 320, '2024-12-01 08:00:00', 6, 'Quarterly packaging restock'),
(4, 1, 4, '2024-10-15 09:00:00', 1, 'Critical item - low stock'),
(5, 2, 450, '2024-12-03 13:00:00', 9, 'Annual safety gear restock'),
(5, 4, 180, '2024-11-28 10:00:00', 8, 'Safety audit requirement'),
(6, 3, 18, '2024-12-07 15:00:00', 7, 'New batch received'),
(7, 5, 35, '2024-11-20 09:30:00', 10, 'Expansion restock'),
(8, 1, 1200, '2024-12-09 08:00:00', 6, 'Large packaging order'),
(9, 2, 6, '2024-11-10 11:00:00', 2, 'Equipment restock'),
(10, 1, 88, '2024-12-02 14:00:00', 1, 'Regular safety restock'),
(10, 3, 34, '2024-12-01 09:00:00', 3, 'Safety compliance'),
(11, 3, 22, '2024-12-06 10:00:00', 7, 'IoT device rollout'),
(12, 1, 2500, '2024-12-10 07:00:00', 6, 'Large box restock');

-- ============================================================
-- TABLE: order (outbound orders)
-- ============================================================
CREATE TABLE IF NOT EXISTS `order` (
    id INT AUTO_INCREMENT PRIMARY KEY,
    order_number VARCHAR(50) UNIQUE NOT NULL,
    customer_name VARCHAR(150) NOT NULL,
    customer_email VARCHAR(150),
    customer_phone VARCHAR(20),
    warehouse_id INT,
    status ENUM('pending', 'processing', 'shipped', 'delivered', 'cancelled') DEFAULT 'pending',
    total_amount DECIMAL(14,2) DEFAULT 0.00,
    shipping_address TEXT,
    notes TEXT,
    created_by INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (warehouse_id) REFERENCES warehouse(id) ON DELETE SET NULL,
    FOREIGN KEY (created_by) REFERENCES employee(id) ON DELETE SET NULL
);

INSERT INTO `order` (order_number, customer_name, customer_email, customer_phone, warehouse_id, status, total_amount, shipping_address, created_by) VALUES
('ORD-2024-001', 'Infosys Ltd', 'procurement@infosys.com', '+91-8011223344', 1, 'delivered', 425000.00, '44 Electronics City, Bengaluru 560100', 1),
('ORD-2024-002', 'Tata Motors', 'stores@tatamotors.com', '+91-8022334455', 2, 'shipped', 189500.00, '1 Auto Complex, Pune 411018', 2),
('ORD-2024-003', 'Flipkart Pvt Ltd', 'ops@flipkart.com', '+91-8033445566', 1, 'processing', 98400.00, 'Flipkart WH, NH-48, Gurugram 122016', 6),
('ORD-2024-004', 'Amazon India', 'vendor@amazon.in', '+91-8044556677', 3, 'pending', 215600.00, 'Amazon FC, Dobespet, Bengaluru 562109', 7),
('ORD-2024-005', 'Myntra Designs', 'supply@myntra.com', '+91-8055667788', 2, 'delivered', 44000.00, 'Myntra WH, Garvebhavi Palya, Bengaluru', 9),
('ORD-2024-006', 'Mahindra & Mahindra', 'store@mahindra.com', '+91-8066778899', 5, 'cancelled', 135000.00, 'Mahindra Towers, Worli, Mumbai 400018', 10),
('ORD-2024-007', 'Reliance Retail', 'ops@relianceretail.com', '+91-8077889900', 1, 'processing', 320000.00, 'Dhirubhai Ambani Centre, BKC, Mumbai', 1),
('ORD-2024-008', 'HCL Technologies', 'proc@hcl.com', '+91-8088990011', 3, 'shipped', 57600.00, 'HCL Techno Park, Sholinganallur, Chennai', 3);

-- ============================================================
-- TABLE: orderitem
-- ============================================================
CREATE TABLE IF NOT EXISTS orderitem (
    id INT AUTO_INCREMENT PRIMARY KEY,
    order_id INT NOT NULL,
    product_id INT NOT NULL,
    quantity INT NOT NULL,
    unit_price DECIMAL(12,2) NOT NULL,
    total_price DECIMAL(14,2) GENERATED ALWAYS AS (quantity * unit_price) STORED,
    FOREIGN KEY (order_id) REFERENCES `order`(id) ON DELETE CASCADE,
    FOREIGN KEY (product_id) REFERENCES product(id) ON DELETE RESTRICT
);

INSERT INTO orderitem (order_id, product_id, quantity, unit_price) VALUES
(1, 1, 20, 8500.00),
(1, 6, 10, 12000.00),
(1, 11, 25, 3200.00),
(2, 4, 2, 45000.00),
(2, 9, 5, 18500.00),
(2, 7, 4, 6800.00),
(3, 2, 15, 4200.00),
(3, 5, 60, 650.00),
(4, 1, 15, 8500.00),
(4, 6, 5, 12000.00),
(4, 11, 10, 3200.00),
(5, 10, 200, 220.00),
(6, 4, 3, 45000.00),
(7, 3, 200, 850.00),
(7, 8, 500, 520.00),
(7, 12, 3000, 45.00),
(8, 11, 18, 3200.00);

-- ============================================================
-- TABLE: bad_stock
-- ============================================================
CREATE TABLE IF NOT EXISTS bad_stock (
    id INT AUTO_INCREMENT PRIMARY KEY,
    product_id INT NOT NULL,
    warehouse_id INT NOT NULL,
    quantity INT NOT NULL,
    reason ENUM('damaged', 'expired', 'defective', 'water_damage', 'fire_damage', 'theft', 'other') NOT NULL,
    description TEXT,
    estimated_loss DECIMAL(14,2),
    reported_by INT,
    status ENUM('reported', 'under_review', 'written_off', 'returned_to_supplier') DEFAULT 'reported',
    reported_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMP NULL,
    FOREIGN KEY (product_id) REFERENCES product(id) ON DELETE RESTRICT,
    FOREIGN KEY (warehouse_id) REFERENCES warehouse(id) ON DELETE RESTRICT,
    FOREIGN KEY (reported_by) REFERENCES employee(id) ON DELETE SET NULL
);

INSERT INTO bad_stock (product_id, warehouse_id, quantity, reason, description, estimated_loss, reported_by, status, reported_at) VALUES
(1, 1, 3, 'damaged', 'Cameras dropped during unloading, lens shattered', 25500.00, 6, 'written_off', '2024-11-05 10:00:00'),
(3, 1, 50, 'water_damage', 'Roof leak in Bay 3 damaged pallet wraps', 42500.00, 1, 'written_off', '2024-10-20 14:30:00'),
(5, 2, 20, 'defective', 'Helmets failed QC - chin straps broken on receipt', 13000.00, 9, 'returned_to_supplier', '2024-11-15 09:00:00'),
(12, 1, 200, 'damaged', 'Forklift crushed stack of boxes in aisle 7', 9000.00, 6, 'written_off', '2024-12-01 11:00:00'),
(10, 3, 15, 'defective', 'Reflective strips peeling off - safety non-compliant', 3300.00, 7, 'under_review', '2024-12-08 13:00:00'),
(2, 1, 2, 'defective', 'Barcode scanners arrived with broken USB ports', 8400.00, 1, 'returned_to_supplier', '2024-11-28 10:30:00'),
(8, 1, 100, 'damaged', 'Bubble wrap rolls compressed and unusable after storage', 52000.00, 6, 'reported', '2024-12-09 08:00:00');

-- ============================================================
-- VIEWS for quick statistics
-- ============================================================
CREATE OR REPLACE VIEW v_stock_summary AS
SELECT 
    p.id AS product_id,
    p.name AS product_name,
    p.sku,
    p.category,
    p.reorder_level,
    p.unit_price,
    COALESCE(SUM(s.quantity), 0) AS total_quantity,
    COALESCE(SUM(s.quantity), 0) * p.unit_price AS stock_value,
    COUNT(DISTINCT s.warehouse_id) AS warehouse_count,
    -- I added this single line below so your next view works perfectly --
    CASE WHEN COALESCE(SUM(s.quantity), 0) <= p.reorder_level THEN 'low' ELSE 'normal' END AS status_check
FROM product p
LEFT JOIN stock s ON p.id = s.product_id
GROUP BY p.id, p.name, p.sku, p.category, p.reorder_level, p.unit_price;

CREATE OR REPLACE VIEW v_low_stock AS
SELECT * FROM v_stock_summary
WHERE total_quantity <= reorder_level AND status_check = 'low'
ORDER BY total_quantity ASC;

-- ============================================================
-- End of database.sql
-- ============================================================