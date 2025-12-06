-- SETUP
CREATE DATABASE ECommerceDB;
USE ECommerceDB;

SET FOREIGN_KEY_CHECKS = 0;

-- -----------------------------------------------------------
-- DDL
-- -----------------------------------------------------------

-- 1. USER
CREATE TABLE USER (
    User_ID INT AUTO_INCREMENT PRIMARY KEY, -- PK, Auto Increment
    Username VARCHAR(50) NOT NULL UNIQUE,
    Name VARCHAR(100) NOT NULL,
    Email VARCHAR(100) UNIQUE,
    Street VARCHAR(100),
    City VARCHAR(50)
);

-- 2. USER_PHONE
CREATE TABLE USER_PHONE (
    User_ID INT,
    Phone_number VARCHAR(15),
    Phone_type VARCHAR(20) CHECK (Phone_type IN ('Mobile', 'Home', 'Work')),
    Is_primary BOOLEAN DEFAULT FALSE,
    PRIMARY KEY (User_ID, Phone_number),
    FOREIGN KEY (User_ID) REFERENCES USER(User_ID)
);

-- 3 & 4. CUSTOMER / SHOP
CREATE TABLE CUSTOMER (
    Customer_ID INT PRIMARY KEY,
    FOREIGN KEY (Customer_ID) REFERENCES USER(User_ID)
);

CREATE TABLE SHOP (
    Shop_ID INT AUTO_INCREMENT PRIMARY KEY,
    User_ID INT NOT NULL UNIQUE,
    Shop_name VARCHAR(100) NOT NULL UNIQUE,
    Location VARCHAR(255),
    FOREIGN KEY (User_ID) REFERENCES USER(User_ID)
);

-- 5. TYPE
CREATE TABLE TYPE (
    Type_ID INT AUTO_INCREMENT PRIMARY KEY,
    Type_name VARCHAR(50) NOT NULL UNIQUE
);

-- 6. PRODUCT
CREATE TABLE PRODUCT (
    Product_ID INT AUTO_INCREMENT PRIMARY KEY,
    Shop_ID INT NOT NULL,
    Type_ID INT NOT NULL,
    Name VARCHAR(200) NOT NULL,
    Price DECIMAL(10,2) CHECK (Price > 0),
    Quantity INT CHECK (Quantity >= 0),
    FOREIGN KEY (Shop_ID) REFERENCES SHOP(Shop_ID),
    FOREIGN KEY (Type_ID) REFERENCES TYPE(Type_ID)
);

-- 7 & 8. SHOPPING_CART / SHOPPING_ORDER
CREATE TABLE SHOPPING_CART (
    Cart_ID INT AUTO_INCREMENT PRIMARY KEY,
    Estimated_cost DECIMAL(10,2) DEFAULT 0,
    Order_quantity INT DEFAULT 0
);

CREATE TABLE SHOPPING_ORDER (
    Order_ID INT AUTO_INCREMENT PRIMARY KEY,
    Order_date DATE DEFAULT (CURRENT_DATE()),
    Delivery_date DATE,
    Address TEXT NOT NULL,
    Total_cost DECIMAL(10,2) CHECK (Total_cost >= 0),
    Status VARCHAR(50) CHECK (Status IN ('CONFIRMATION', 'DELIVERY', 'SUCCESS')),
    CHECK (Delivery_date >= Order_date)
);

-- 9. COMMENT
CREATE TABLE COMMENT (
    Comment_ID INT AUTO_INCREMENT PRIMARY KEY,
    Customer_ID INT NOT NULL,
    Product_ID INT NOT NULL,
    Content TEXT,
    Rate INT CHECK (Rate BETWEEN 1 AND 5),
    Comment_date DATE,
    FOREIGN KEY (Customer_ID) REFERENCES CUSTOMER(Customer_ID),
    FOREIGN KEY (Product_ID) REFERENCES PRODUCT(Product_ID)
);

-- 10. PAYMENT_METHOD
CREATE TABLE PAYMENT_METHOD (
    Order_ID INT PRIMARY KEY,
    Payment_type VARCHAR(20) CHECK (Payment_type IN('COD', 'BANKING')),
    FOREIGN KEY (Order_ID) REFERENCES SHOPPING_ORDER(Order_ID) ON DELETE CASCADE
);

-- 11 & 12. COD / BANKING 
CREATE TABLE COD (
    Order_ID INT PRIMARY KEY,
    FOREIGN KEY (Order_ID) REFERENCES PAYMENT_METHOD(Order_ID)
);

CREATE TABLE BANKING (
    Order_ID INT PRIMARY KEY,
    Bank_name VARCHAR(100),
    Account_number VARCHAR(50),
    FOREIGN KEY (Order_ID) REFERENCES PAYMENT_METHOD(Order_ID)
);

-- 13. VOUCHER (Auto Increment)
CREATE TABLE VOUCHER (
    Voucher_ID INT AUTO_INCREMENT PRIMARY KEY,
    Value DECIMAL(10,2),
    Remaining_Date DATE
);

-- 14 & 15. COUPON / FREESHIP 
CREATE TABLE COUPON (
    Voucher_ID INT PRIMARY KEY,
    FOREIGN KEY (Voucher_ID) REFERENCES VOUCHER(Voucher_ID)
);

CREATE TABLE FREESHIP (
    Voucher_ID INT PRIMARY KEY,
    FOREIGN KEY (Voucher_ID) REFERENCES VOUCHER(Voucher_ID)
);

-- 16. VOUCHER_SCOPE (XOR Scope)
CREATE TABLE VOUCHER_SCOPE (
    Voucher_ID INT PRIMARY KEY,
    ScopeType ENUM('SHOP', 'TYPE') NOT NULL,
    Shop_ID INT,
    Type_ID INT,
    FOREIGN KEY (Voucher_ID) REFERENCES VOUCHER(Voucher_ID),
    FOREIGN KEY (Shop_ID) REFERENCES SHOP(Shop_ID),
    FOREIGN KEY (Type_ID) REFERENCES TYPE(Type_ID),
    -- CHECK Constraint for XOR: Shop_ID or Type_ID
    CHECK (
        (ScopeType = 'SHOP' AND Shop_ID IS NOT NULL AND Type_ID IS NULL) OR
        (ScopeType = 'TYPE' AND Type_ID IS NOT NULL AND Shop_ID IS NULL)
    )
);

-- 17. OWN (1:1 Customer - Cart)
CREATE TABLE OWN (
    Customer_ID INT PRIMARY KEY,
    Cart_ID INT UNIQUE NOT NULL,
    FOREIGN KEY (Customer_ID) REFERENCES CUSTOMER(Customer_ID),
    FOREIGN KEY (Cart_ID) REFERENCES SHOPPING_CART(Cart_ID)
);

-- 18. ORIGINATES_FROM (1:1 Order - Cart)
CREATE TABLE ORIGINATES_FROM (
    Order_ID INT PRIMARY KEY,
    Cart_ID INT UNIQUE NOT NULL,
    FOREIGN KEY (Order_ID) REFERENCES SHOPPING_ORDER(Order_ID),
    FOREIGN KEY (Cart_ID) REFERENCES SHOPPING_CART(Cart_ID)
);

-- 19. CART_ITEM (N:M)
CREATE TABLE CART_ITEM (
    Cart_ID INT,
    Product_ID INT,
    quantity INT CHECK (quantity > 0),
    PRIMARY KEY (Cart_ID, Product_ID),
    FOREIGN KEY (Cart_ID) REFERENCES SHOPPING_CART(Cart_ID),
    FOREIGN KEY (Product_ID) REFERENCES PRODUCT(Product_ID)
);

-- 20. ORDER_ITEM (N:M)
CREATE TABLE ORDER_ITEM (
    Order_ID INT,
    Product_ID INT,
    quantity INT CHECK (quantity > 0),
    PRIMARY KEY (Order_ID, Product_ID),
    FOREIGN KEY (Order_ID) REFERENCES SHOPPING_ORDER(Order_ID),
    FOREIGN KEY (Product_ID) REFERENCES PRODUCT(Product_ID)
);

-- 21. APPLY_FREESHIP (1 Order max 1 Freeship)
CREATE TABLE APPLY_FREESHIP (
    Voucher_ID INT,
    Order_ID INT UNIQUE NOT NULL,
    PRIMARY KEY (Order_ID),
    FOREIGN KEY (Voucher_ID) REFERENCES FREESHIP(Voucher_ID),
    FOREIGN KEY (Order_ID) REFERENCES SHOPPING_ORDER(Order_ID)
);

-- 22. APPLY_COUPON (1 Order max 1 Coupon)
CREATE TABLE APPLY_COUPON (
    Voucher_ID INT,
    Order_ID INT UNIQUE NOT NULL,
    PRIMARY KEY (Order_ID),
    FOREIGN KEY (Voucher_ID) REFERENCES COUPON(Voucher_ID),
    FOREIGN KEY (Order_ID) REFERENCES SHOPPING_ORDER(Order_ID)
);
-- -----------------------------------------------------------
-- DML
-- -----------------------------------------------------------

-- 1. USER
INSERT INTO USER (Username, Name, Email, Street, City) VALUES
('buyer_alice', 'Alice Smith', 'alice@mail.com', '101 ABC Street', 'Ho Chi Minh City'),
('seller_bob', 'Bob Johnson', 'bob@shop.com', '202 XYZ Road', 'Ha Noi'),
('customer_charlie', 'Charlie Brown', 'charlie@web.com', '303 PQR Lane', 'Da Nang'),
('admin_diana', 'Diana Prince', 'diana@corp.com', '404 LMN Ave', 'Ho Chi Minh City'),
('user_eve', 'Eve Adams', 'eve@mail.com', '505 STU Way', 'Ho Chi Minh City');

-- 2. USER_PHONE
INSERT INTO USER_PHONE (User_ID, Phone_number, Phone_type, Is_primary) VALUES
(1, '0901000111', 'Mobile', TRUE), (1, '028111222', 'Home', FALSE),
(2, '0902000222', 'Mobile', TRUE), (3, '0903000333', 'Mobile', TRUE),
(5, '0905555555', 'Mobile', TRUE);

-- 3. CUSTOMER
INSERT INTO CUSTOMER (Customer_ID) VALUES (1), (3), (4), (5);

-- 4. SHOP
INSERT INTO SHOP (User_ID, Shop_name, Location) VALUES
(2, 'Bob’s Gadgets', 'Ha Noi'),
(3, 'Charlie’s Comics', 'Da Nang'),
(4, 'Diana’s Dresses', 'Ho Chi Minh City'),
(5, 'Eve’s Electronics', 'Ho Chi Minh City');

-- 5. TYPE
INSERT INTO TYPE (Type_name) VALUES
('ELECTRONICS'), ('APPAREL'), ('BOOKS'), ('HOME_LIVING'), ('BEAUTY');

-- 6. PRODUCT
INSERT INTO PRODUCT (Shop_ID, Type_ID, Name, Price, Quantity) VALUES
(1, 1, 'Laptop Pro', 1500.00, 10), (1, 2, 'T-shirt Cotton', 20.50, 50),
(1, 3, 'The Great Gatsby', 15.00, 30), (1, 4, 'Coffee Mug Set', 12.00, 100),
(1, 5, 'Sunscreen SPF50', 25.00, 20);

-- 7. VOUCHER
INSERT INTO VOUCHER (Value, Remaining_Date) VALUES
(10.00, '2025-12-31'), (5.00, '2026-01-15'), (20.00, '2025-11-30'),
(100.00, '2025-12-01'), (1.00, '2025-12-25'),
(5.00, '2026-02-01'), 
(20.00, '2026-03-01'), 
(15.00, '2026-04-01'); 

-- 8 & 9. COUPON / FREESHIP
INSERT INTO COUPON (Voucher_ID) VALUES (1), (3), (5), (6);

INSERT INTO FREESHIP (Voucher_ID) VALUES (2), (4), (7), (8);

-- 10. VOUCHER_SCOPE
INSERT INTO VOUCHER_SCOPE (Voucher_ID, ScopeType, Shop_ID, Type_ID) VALUES
(1, 'SHOP', 1, NULL), (2, 'SHOP', 1, NULL),
(3, 'TYPE', NULL, 1), (4, 'TYPE', NULL, 2), 
(6, 'SHOP', 2, NULL), 
(7, 'TYPE', NULL, 3), 
(8, 'TYPE', NULL, 4); 

-- 11. SHOPPING_CART
INSERT INTO SHOPPING_CART (Cart_ID) VALUES (1), (2), (3), (4);

-- 12. OWN (Customer -> Cart)
INSERT INTO OWN (Customer_ID, Cart_ID) VALUES (1, 1), (3, 2), (4, 3), (5, 4);

-- 13. SHOPPING_ORDER
INSERT INTO SHOPPING_ORDER (Order_ID, Order_date, Delivery_date, Address, Total_cost, Status) VALUES
(1, '2025-10-01', '2025-10-05', 'Alice Home Address', 1515.00, 'SUCCESS'),
(2, '2025-10-10', '2025-10-14', 'Charlie Home Address', 61.50, 'DELIVERY'),
(3, '2025-11-20', '2025-11-25', 'Diana Home Address', 25.00, 'CONFIRMATION'),
(4, '2025-11-24', '2025-11-27', 'Eve Home Address', 30.00, 'CONFIRMATION'),
(5,'2025-12-01', '2025-12-05', 'New Order 5 Address', 80.00, 'DELIVERY'), 
(6,'2025-12-02', '2025-12-06', 'New Order 6 Address', 120.00, 'SUCCESS');

-- 14. ORIGINATES_FROM
INSERT INTO ORIGINATES_FROM (Order_ID, Cart_ID) VALUES (1, 1), (2, 2), (3, 3), (4, 4);

-- 15. ORDER_ITEM
INSERT INTO ORDER_ITEM (Order_ID, Product_ID, quantity) VALUES
(1, 1, 1), (1, 4, 2), (2, 2, 3), (3, 5, 1), (4, 3, 2),(5, 1, 1), (5, 3, 4),(6, 2, 2), (6, 5, 3);

-- 16. PAYMENT_METHOD
INSERT INTO PAYMENT_METHOD (Order_ID, Payment_type) VALUES
(1, 'BANKING'), (2, 'COD'), (3, 'COD'), (4, 'BANKING'), (5, 'COD'), (6, 'BANKING');

-- 17 & 18. COD / BANKING
INSERT INTO BANKING (Order_ID, Bank_name, Account_number) VALUES
(1, 'VCB', '1234567890'), (4, 'ACB', '0987654321'),(6, 'Techcombank', '1122334455');
INSERT INTO COD (Order_ID) VALUES (2), (3), (5);

-- 19 & 20. APPLY_FREESHIP / APPLY_COUPON
INSERT INTO APPLY_FREESHIP (Voucher_ID, Order_ID) VALUES (2, 1);
INSERT INTO APPLY_COUPON (Voucher_ID, Order_ID) VALUES (1, 1);

-- 21. COMMENT
INSERT INTO COMMENT (Comment_ID, Customer_ID, Product_ID, Content, Rate, Comment_date) VALUES
(1, 1, 1, 'Laptop is excellent!', 5, '2025-10-06'),
(3,3, 2, 'Good quality T-shirt.', 4, '2025-10-15'),
(4,4, 5, 'Sunscreen delivered quickly.', 5, '2025-11-26'),
(2, 1, 4, 'Mugs arrived intact.', 4, '2025-10-06');
-- 22.CART_ITEM
INSERT INTO CART_ITEM (Cart_ID, Product_ID, quantity) VALUES
(2, 3, 1), 
(3, 5, 2), 
(4, 1, 1), 
(2, 4, 3); 



SET FOREIGN_KEY_CHECKS = 1;
CREATE USER 'sManager'@'%' IDENTIFIED BY '123456789@K';
GRANT ALL PRIVILEGES ON ECommerceDB.* TO 'sManager'@'%' WITH GRANT OPTION;
FLUSH PRIVILEGES;
