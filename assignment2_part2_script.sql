-- CHỌN DATABASE CỦA BẠN
USE EcommerceDB;

-- Đổi delimiter để tạo function/procedure/trigger
DELIMITER $$

/* =====================================================
   FUNCTION 1: fn_customer_total_spent
   → Tổng tiền mà 1 customer đã chi (SUM Total_cost)
   Bảng dùng: CUSTOMER, OWN, SHOPPING_CART, ORIGINATES_FROM, SHOPPING_ORDER
   Thể hiện:
   - JOIN nhiều bảng
   - WHERE dùng input param
   - Aggregate SUM
   - Validate input bằng IF + SIGNAL
   ===================================================== */

DROP FUNCTION IF EXISTS fn_customer_total_spent $$
CREATE FUNCTION fn_customer_total_spent(p_customer_id INT)
RETURNS DECIMAL(10,2)
DETERMINISTIC
BEGIN
    DECLARE v_total DECIMAL(10,2);

    IF p_customer_id IS NULL OR p_customer_id <= 0 THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Invalid customer id';
    END IF;

    SELECT COALESCE(SUM(o.Total_cost), 0)
    INTO v_total
    FROM CUSTOMER c
    JOIN OWN ow ON ow.Customer_ID = c.Customer_ID
    JOIN SHOPPING_CART sc ON sc.Cart_ID = ow.Cart_ID
    JOIN ORIGINATES_FROM ofr ON ofr.Cart_ID = sc.Cart_ID
    JOIN SHOPPING_ORDER o ON o.Order_ID = ofr.Order_ID
    WHERE c.Customer_ID = p_customer_id;

    RETURN v_total;
END $$


/* =====================================================
   FUNCTION 2: fn_product_avg_rating
   → Rating trung bình của 1 sản phẩm (AVG Rate)
   Bảng dùng: COMMENT
   Thể hiện:
   - WHERE dùng input param
   - Aggregate AVG + ROUND
   - Validate input bằng IF + SIGNAL
   ===================================================== */

DROP FUNCTION IF EXISTS fn_product_avg_rating $$
CREATE FUNCTION fn_product_avg_rating(p_product_id INT)
RETURNS DECIMAL(3,2)
DETERMINISTIC
BEGIN
    DECLARE v_avg DECIMAL(3,2);

    IF p_product_id IS NULL OR p_product_id <= 0 THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Invalid product id';
    END IF;

    SELECT ROUND(AVG(Rate), 2)
    INTO v_avg
    FROM COMMENT
    WHERE Product_ID = p_product_id;

    RETURN COALESCE(v_avg, 0);
END $$





/* =====================================================
   PROCEDURE 1: sp_get_orders_by_status_date
   → Lấy danh sách đơn hàng theo status + khoảng ngày
   Bảng dùng: SHOPPING_ORDER, ORIGINATES_FROM, SHOPPING_CART, OWN, CUSTOMER, USER
   Thể hiện:
   - JOIN ≥ 2 bảng
   - WHERE + ORDER BY
   - Input param dùng trong WHERE
   - IF để validate input (p_from, p_to)
   ===================================================== */

DROP PROCEDURE IF EXISTS sp_get_orders_by_status_date $$
CREATE PROCEDURE sp_get_orders_by_status_date(
    IN p_status VARCHAR(50),
    IN p_from DATE,
    IN p_to   DATE
)
BEGIN
    IF p_from IS NULL OR p_to IS NULL THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'From/To date cannot be NULL';
    END IF;

    IF p_from > p_to THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'From date must be <= To date';
    END IF;

    SELECT o.Order_ID,
           o.Order_date,
           o.Delivery_date,
           o.Address,
           o.Total_cost,
           o.Status,
           u.Name AS CustomerName
    FROM SHOPPING_ORDER o
    LEFT JOIN ORIGINATES_FROM ofr ON ofr.Order_ID = o.Order_ID
    LEFT JOIN SHOPPING_CART sc ON sc.Cart_ID = ofr.Cart_ID
    LEFT JOIN OWN ow ON ow.Cart_ID = sc.Cart_ID
    LEFT JOIN CUSTOMER c ON c.Customer_ID = ow.Customer_ID
    LEFT JOIN USER u ON u.User_ID = c.Customer_ID
    WHERE (p_status IS NULL OR o.Status = p_status)
      AND o.Order_date BETWEEN p_from AND p_to
    ORDER BY o.Order_date DESC;
END $$


/* =====================================================
   PROCEDURE 2: sp_get_top_products_by_type
   → Top sản phẩm theo Type, có tổng quantity bán ≥ p_min_qty
   Bảng dùng: ORDER_ITEM, PRODUCT, TYPE
   Thể hiện:
   - JOIN nhiều bảng
   - GROUP BY + HAVING + aggregate SUM
   - Input param trong WHERE + HAVING
   - IF để validate Type & p_min_qty
   ===================================================== */

DROP PROCEDURE IF EXISTS sp_get_top_products_by_type $$
CREATE PROCEDURE sp_get_top_products_by_type(
    IN p_type_id INT,
    IN p_min_qty INT
)
BEGIN
    IF p_min_qty IS NULL OR p_min_qty <= 0 THEN
        SET p_min_qty = 1;
    END IF;

    IF NOT EXISTS (SELECT 1 FROM TYPE WHERE Type_ID = p_type_id) THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Type does not exist';
    END IF;

    SELECT p.Product_ID,
           p.Name,
           t.Type_name,
           SUM(oi.quantity) AS total_sold
    FROM ORDER_ITEM oi
    JOIN PRODUCT p ON p.Product_ID = oi.Product_ID
    JOIN TYPE t ON t.Type_ID = p.Type_ID
    WHERE p.Type_ID = p_type_id
    GROUP BY p.Product_ID, p.Name, t.Type_name
    HAVING SUM(oi.quantity) >= p_min_qty
    ORDER BY total_sold DESC;
END $$


/* =====================================================
   FUNCTION 3: fn_customer_order_count_in_range
   → Đếm số đơn hàng của một customer trong một khoảng ngày
   Bảng dùng: CUSTOMER, OWN, SHOPPING_CART, ORIGINATES_FROM, SHOPPING_ORDER
   Thể hiện:
   - JOIN nhiều bảng
   - WHERE dùng input parameters
   - Aggregate COUNT(DISTINCT Order_ID)
   - IF để validate customer_id và khoảng ngày (p_from, p_to)
   ===================================================== */

DROP FUNCTION IF EXISTS fn_customer_order_count_in_range $$
CREATE FUNCTION fn_customer_order_count_in_range(
    p_customer_id INT,
    p_from DATE,
    p_to   DATE
)
RETURNS INT
DETERMINISTIC
BEGIN
    DECLARE v_count INT;

    -- Validate customer ID
    IF p_customer_id IS NULL OR p_customer_id <= 0 THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Invalid customer id';
    END IF;

    -- Validate date range
    IF p_from IS NULL OR p_to IS NULL THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'From/To date cannot be NULL';
    END IF;

    IF p_from > p_to THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'From date must be <= To date';
    END IF;

    -- Đếm số đơn hàng trong khoảng ngày
    SELECT COUNT(DISTINCT o.Order_ID)
    INTO v_count
    FROM CUSTOMER c
    JOIN OWN ow ON ow.Customer_ID = c.Customer_ID
    JOIN SHOPPING_CART sc ON sc.Cart_ID = ow.Cart_ID
    JOIN ORIGINATES_FROM ofr ON ofr.Cart_ID = sc.Cart_ID
    JOIN SHOPPING_ORDER o ON o.Order_ID = ofr.Order_ID
    WHERE c.Customer_ID = p_customer_id
      AND o.Order_date BETWEEN p_from AND p_to;

    RETURN COALESCE(v_count, 0);
END $$



/* =====================================================
   TRIGGER 1: trg_check_stock_before_order_item_insert
   → BUSINESS RULE:
     - Không cho insert ORDER_ITEM nếu:
       + quantity <= 0
       + hoặc > stock hiện tại của PRODUCT
   Bảng dùng: ORDER_ITEM, PRODUCT
   Thỏa yêu cầu: "ít nhất 1 trigger enforce business rule"
   ===================================================== */

DROP TRIGGER IF EXISTS trg_check_stock_before_order_item_insert $$
CREATE TRIGGER trg_check_stock_before_order_item_insert
BEFORE INSERT ON ORDER_ITEM
FOR EACH ROW
BEGIN
    DECLARE v_stock INT;

    SELECT Quantity
    INTO v_stock
    FROM PRODUCT
    WHERE Product_ID = NEW.Product_ID;

    IF v_stock IS NULL THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Product does not exist';
    END IF;

    IF NEW.quantity <= 0 THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Quantity must be > 0';
    END IF;

    IF NEW.quantity > v_stock THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Not enough stock for this product';
    END IF;
END $$


/* =====================================================
   TRIGGER 2: trg_update_order_total_after_order_item_insert
   → DERIVED COLUMN:
     - Sau khi thêm ORDER_ITEM, tự tính lại SHOPPING_ORDER.Total_cost
       = SUM(quantity * Price) của tất cả ORDER_ITEM trong order đó
   Bảng dùng: ORDER_ITEM, PRODUCT, SHOPPING_ORDER
   Thỏa yêu cầu: "ít nhất 1 trigger generate derived column value"
   ===================================================== */

DROP TRIGGER IF EXISTS trg_update_order_total_after_order_item_insert $$
CREATE TRIGGER trg_update_order_total_after_order_item_insert
AFTER INSERT ON ORDER_ITEM
FOR EACH ROW
BEGIN
    DECLARE v_total DECIMAL(10,2);

    SELECT COALESCE(SUM(oi.quantity * p.Price), 0)
    INTO v_total
    FROM ORDER_ITEM oi
    JOIN PRODUCT p ON p.Product_ID = oi.Product_ID
    WHERE oi.Order_ID = NEW.Order_ID;

    UPDATE SHOPPING_ORDER
    SET Total_cost = v_total
    WHERE Order_ID = NEW.Order_ID;
END $$


/* =====================================================
   TRIGGER 3: trg_validate_order_dates_before_insert
   → Tự động gán Order_date/Delivery_date & kiểm tra logic ngày
   Bảng dùng: SHOPPING_ORDER
   Thể hiện:
   - BEFORE INSERT trigger
   - Generated/derived values:
       + Nếu Order_date IS NULL  → set = CURDATE()
       + Nếu Delivery_date IS NULL → set = Order_date + 3 ngày
   - Business rule:
       + Delivery_date phải >= Order_date, nếu không → SIGNAL lỗi
   ===================================================== */

DROP TRIGGER IF EXISTS trg_validate_order_dates_before_insert $$
CREATE TRIGGER trg_validate_order_dates_before_insert
BEFORE INSERT ON SHOPPING_ORDER
FOR EACH ROW
BEGIN
    -- Nếu không nhập Order_date thì mặc định là hôm nay
    IF NEW.Order_date IS NULL THEN
        SET NEW.Order_date = CURDATE();
    END IF;

    -- Nếu không nhập Delivery_date thì mặc định +3 ngày
    IF NEW.Delivery_date IS NULL THEN
        SET NEW.Delivery_date = DATE_ADD(NEW.Order_date, INTERVAL 3 DAY);
    END IF;

    -- Business rule: Delivery_date không được < Order_date
    IF NEW.Delivery_date < NEW.Order_date THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Delivery_date must be >= Order_date';
    END IF;
END $$


-- Trả delimiter về mặc định
DELIMITER ;
