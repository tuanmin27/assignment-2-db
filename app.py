# app.py
from flask import Flask, render_template, request, redirect, url_for, session, flash
from db import get_connection, DB_CONFIG

app = Flask(__name__)
app.secret_key = "super-secret-key"  # đổi chuỗi khác tuỳ ý

# ====== Middleware nhỏ: bắt buộc login ======
def login_required(view_func):
    def wrapper(*args, **kwargs):
        if not session.get("logged_in"):
            return redirect(url_for("login"))
        return view_func(*args, **kwargs)
    wrapper.__name__ = view_func.__name__
    return wrapper

# ====== Trang chủ ======
@app.route("/")
def index():
    if session.get("logged_in"):
        return redirect(url_for("product_list"))
    return redirect(url_for("login"))

# ====== LOGIN ======
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        # Đề yêu cầu login bằng user sManager
        if username == DB_CONFIG["user"] and password == DB_CONFIG["password"]:
            session["logged_in"] = True
            session["username"] = username
            flash("Đăng nhập thành công!", "success")
            return redirect(url_for("product_list"))
        else:
            flash("Sai tài khoản hoặc mật khẩu sManager", "danger")

    return render_template("login.html")

# ====== LOGOUT ======
@app.route("/logout")
def logout():
    session.clear()
    flash("Đã logout", "info")
    return redirect(url_for("login"))

# ====== Lấy danh sách Type & Shop để dùng cho filter/form ======
def get_all_types():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT Type_ID, Type_name FROM TYPE ORDER BY Type_name")
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return rows

def get_all_shops():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT Shop_ID, Shop_name FROM SHOP ORDER BY Shop_name")
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return rows

# ====== LIST PRODUCT + FILTER + SORT ======
@app.route("/products")
@login_required
def product_list():
    search = request.args.get("q", "")
    type_id = request.args.get("type_id")
    shop_id = request.args.get("shop_id")
    sort = request.args.get("sort")  # PRICE_ASC, PRICE_DESC, NAME_ASC, NAME_DESC

    base_sql = """
        SELECT p.Product_ID, p.Name, p.Price, p.Quantity,
               t.Type_name, s.Shop_name
        FROM PRODUCT p
        JOIN TYPE t ON t.Type_ID = p.Type_ID
        JOIN SHOP s ON s.Shop_ID = p.Shop_ID
    """
    conditions = []
    params = []

    if search:
        conditions.append("p.Name LIKE %s")
        params.append(f"%{search}%")
    if type_id:
        conditions.append("p.Type_ID = %s")
        params.append(type_id)
    if shop_id:
        conditions.append("p.Shop_ID = %s")
        params.append(shop_id)

    if conditions:
        base_sql += " WHERE " + " AND ".join(conditions)

    # Ánh xạ sort param -> ORDER BY
    if sort == "PRICE_ASC":
        base_sql += " ORDER BY p.Price ASC"
    elif sort == "PRICE_DESC":
        base_sql += " ORDER BY p.Price DESC"
    elif sort == "NAME_DESC":
        base_sql += " ORDER BY p.Name DESC"
    else:  # mặc định NAME_ASC
        base_sql += " ORDER BY p.Name ASC"

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(base_sql, params)
    products = cursor.fetchall()
    cursor.close()
    conn.close()

    types = get_all_types()
    shops = get_all_shops()

    return render_template(
        "products.html",
        products=products,
        types=types,
        shops=shops,
        search=search,
        selected_type=type_id,
        selected_shop=shop_id,
        sort=sort,
    )

# ====== CREATE PRODUCT ======
@app.route("/products/new", methods=["GET", "POST"])
@login_required
def product_create():
    types = get_all_types()
    shops = get_all_shops()

    if request.method == "POST":
        name = request.form.get("name")
        price = request.form.get("price")
        quantity = request.form.get("quantity")
        shop_id = request.form.get("shop_id")
        type_id = request.form.get("type_id")

        # Validate đơn giản
        if not name or not price or not quantity or not shop_id or not type_id:
            flash("Vui lòng nhập đầy đủ thông tin", "danger")
            return render_template("product_form.html", types=types, shops=shops, product=None)

        try:
            price = float(price)
            quantity = int(quantity)
        except ValueError:
            flash("Price phải là số, Quantity phải là số nguyên", "danger")
            return render_template("product_form.html", types=types, shops=shops, product=None)

        conn = get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                INSERT INTO PRODUCT (Name, Price, Quantity, Shop_ID, Type_ID)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (name, price, quantity, shop_id, type_id),
            )
            conn.commit()
            flash("Thêm sản phẩm thành công", "success")
            return redirect(url_for("product_list"))
        except Exception as e:
            conn.rollback()
            flash(f"Lỗi khi thêm sản phẩm: {e}", "danger")
        finally:
            cursor.close()
            conn.close()

    return render_template("product_form.html", types=types, shops=shops, product=None)


# ====== EDIT PRODUCT ======
@app.route("/products/<int:product_id>/edit", methods=["GET", "POST"])
@login_required
def product_edit(product_id):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        "SELECT Product_ID, Name, Price, Quantity, Shop_ID, Type_ID FROM PRODUCT WHERE Product_ID = %s",
        (product_id,),
    )
    product = cursor.fetchone()
    cursor.close()
    conn.close()

    if not product:
        flash("Không tìm thấy sản phẩm", "warning")
        return redirect(url_for("product_list"))

    types = get_all_types()
    shops = get_all_shops()

    if request.method == "POST":
        name = request.form.get("name")
        price = request.form.get("price")
        quantity = request.form.get("quantity")
        shop_id = request.form.get("shop_id")
        type_id = request.form.get("type_id")

        if not name or not price or not quantity or not shop_id or not type_id:
            flash("Vui lòng nhập đầy đủ thông tin", "danger")
            return render_template("product_form.html", types=types, shops=shops, product=product)

        try:
            price = float(price)
            quantity = int(quantity)
        except ValueError:
            flash("Price phải là số, Quantity phải là số nguyên", "danger")
            return render_template("product_form.html", types=types, shops=shops, product=product)

        conn = get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                UPDATE PRODUCT
                SET Name = %s, Price = %s, Quantity = %s, Shop_ID = %s, Type_ID = %s
                WHERE Product_ID = %s
                """,
                (name, price, quantity, shop_id, type_id, product_id),
            )
            conn.commit()
            flash("Cập nhật sản phẩm thành công", "success")
            return redirect(url_for("product_list"))
        except Exception as e:
            conn.rollback()
            flash(f"Lỗi khi cập nhật sản phẩm: {e}", "danger")
        finally:
            cursor.close()
            conn.close()

    return render_template("product_form.html", types=types, shops=shops, product=product)


# ====== DELETE PRODUCT ======
@app.route("/products/<int:product_id>/delete", methods=["POST"])
@login_required
def product_delete(product_id):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM PRODUCT WHERE Product_ID = %s", (product_id,))
        conn.commit()
        flash("Đã xoá sản phẩm", "info")
    except Exception as e:
        conn.rollback()
        flash(f"Lỗi khi xoá (có thể do ràng buộc FK): {e}", "danger")
    finally:
        cursor.close()
        conn.close()

    return redirect(url_for("product_list"))

# ====== REPORT: Top product theo Type (gọi SP) ======
@app.route("/reports/top-products", methods=["GET", "POST"])
@login_required
def report_top_products():
    types = get_all_types()
    results = None
    selected_type = None
    min_qty = None

    if request.method == "POST":
        selected_type = request.form.get("type_id")
        min_qty = request.form.get("min_qty") or "1"

        if not selected_type:
            flash("Hãy chọn Type", "danger")
        else:
            try:
                min_qty_int = int(min_qty)
            except ValueError:
                flash("Min quantity phải là số nguyên", "danger")
                min_qty_int = 1

            conn = get_connection()
            cursor = conn.cursor(dictionary=True)
            try:
                # Gọi stored procedure
                cursor.callproc("sp_get_top_products_by_type", [int(selected_type), min_qty_int])

                for result in cursor.stored_results():
                    results = result.fetchall()

            except Exception as e:
                flash(f"Lỗi khi gọi SP: {e}", "danger")
            finally:
                cursor.close()
                conn.close()

    return render_template(
        "report_top_products.html",
        types=types,
        results=results,
        selected_type=selected_type,
        min_qty=min_qty,
    )

# ==========================
#  HỆ THỐNG QUẢN LÝ ĐƠN HÀNG
# ==========================

STATUS_CHOICES = ["CONFIRMATION", "DELIVERY", "SUCCESS"]

# LIST ORDERS + FILTER
@app.route("/orders")
@login_required
def order_list():
    status = request.args.get("status")
    date_from = request.args.get("date_from")
    date_to = request.args.get("date_to")

    sql = """
        SELECT Order_ID, Order_date, Delivery_date, Status, Total_cost, Address
        FROM SHOPPING_ORDER
        WHERE 1=1
    """
    params = []

    if status:
        sql += " AND Status = %s"
        params.append(status)

    if date_from:
        sql += " AND Order_date >= %s"
        params.append(date_from)

    if date_to:
        sql += " AND Order_date <= %s"
        params.append(date_to)

    sql += " ORDER BY Order_date DESC"

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(sql, params)
    orders = cursor.fetchall()
    cursor.close()
    conn.close()

    return render_template(
        "orders.html",
        orders=orders,
        status_choices=STATUS_CHOICES,
        selected_status=status,
        date_from=date_from,
        date_to=date_to,
    )


# TẠO ĐƠN HÀNG MỚI
@app.route("/orders/new", methods=["GET", "POST"])
@login_required
def order_create():
    if request.method == "POST":
        address = request.form.get("address")
        status = request.form.get("status") or "CONFIRMATION"

        if not address:
            flash("Vui lòng nhập địa chỉ giao hàng", "danger")
            return render_template(
                "order_form.html",
                status_choices=STATUS_CHOICES,
                order=None,
            )

        if status not in STATUS_CHOICES:
            flash("Trạng thái không hợp lệ", "danger")
            return render_template(
                "order_form.html",
                status_choices=STATUS_CHOICES,
                order=None,
            )

        conn = get_connection()
        cursor = conn.cursor()
        try:
            # Không set Order_date, Delivery_date, Total_cost
            # → trigger & default trong DB sẽ tự xử lý
            cursor.execute(
                """
                INSERT INTO SHOPPING_ORDER (Address, Status)
                VALUES (%s, %s)
                """,
                (address, status),
            )
            conn.commit()
            new_id = cursor.lastrowid
            flash(f"Tạo đơn hàng #{new_id} thành công", "success")
            return redirect(url_for("order_detail", order_id=new_id))
        except Exception as e:
            conn.rollback()
            flash(f"Lỗi khi tạo đơn hàng: {e}", "danger")
        finally:
            cursor.close()
            conn.close()

    return render_template(
        "order_form.html",
        status_choices=STATUS_CHOICES,
        order=None,
    )


# XEM CHI TIẾT ĐƠN HÀNG (Order + Order Items)
@app.route("/orders/<int:order_id>")
@login_required
def order_detail(order_id):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    # Lấy thông tin chính của đơn
    cursor.execute(
        """
        SELECT Order_ID, Order_date, Delivery_date, Status, Total_cost, Address
        FROM SHOPPING_ORDER
        WHERE Order_ID = %s
        """,
        (order_id,),
    )
    order = cursor.fetchone()

    if not order:
        cursor.close()
        conn.close()
        flash("Không tìm thấy đơn hàng", "warning")
        return redirect(url_for("order_list"))

    # Lấy các item trong đơn
    cursor.execute(
        """
        SELECT oi.Product_ID, p.Name AS ProductName,
               oi.quantity,
               p.Price,
               (oi.quantity * p.Price) AS LineTotal
        FROM ORDER_ITEM oi
        JOIN PRODUCT p ON p.Product_ID = oi.Product_ID
        WHERE oi.Order_ID = %s
        """,
        (order_id,),
    )
    items = cursor.fetchall()

    # Lấy danh sách product cho form "Add item"
    cursor.execute(
        "SELECT Product_ID, Name FROM PRODUCT ORDER BY Name"
    )
    products = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template(
        "order_detail.html",
        order=order,
        items=items,
        products=products,
        status_choices=STATUS_CHOICES,
    )


# CẬP NHẬT TRẠNG THÁI ĐƠN HÀNG
@app.route("/orders/<int:order_id>/update-status", methods=["POST"])
@login_required
def order_update_status(order_id):
    new_status = request.form.get("status")

    if new_status not in STATUS_CHOICES:
        flash("Trạng thái không hợp lệ", "danger")
        return redirect(url_for("order_detail", order_id=order_id))

    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "UPDATE SHOPPING_ORDER SET Status = %s WHERE Order_ID = %s",
            (new_status, order_id),
        )
        conn.commit()
        flash("Cập nhật trạng thái đơn hàng thành công", "success")
    except Exception as e:
        conn.rollback()
        flash(f"Lỗi khi cập nhật trạng thái: {e}", "danger")
    finally:
        cursor.close()
        conn.close()

    return redirect(url_for("order_detail", order_id=order_id))


# THÊM ITEM VÀO ĐƠN HÀNG
@app.route("/orders/<int:order_id>/add-item", methods=["POST"])
@login_required
def order_add_item(order_id):
    product_id = request.form.get("product_id")
    quantity = request.form.get("quantity")

    if not product_id or not quantity:
        flash("Vui lòng chọn sản phẩm và số lượng", "danger")
        return redirect(url_for("order_detail", order_id=order_id))

    try:
        qty_int = int(quantity)
    except ValueError:
        flash("Số lượng phải là số nguyên", "danger")
        return redirect(url_for("order_detail", order_id=order_id))

    conn = get_connection()
    cursor = conn.cursor()
    try:
        # Trigger trg_check_stock_before_order_item_insert
        # sẽ kiểm tra stock & quantity > 0
        # Trigger trg_update_order_total_after_order_item_insert
        # sẽ cập nhật Total_cost cho SHOPPING_ORDER
        cursor.execute(
            """
            INSERT INTO ORDER_ITEM (Order_ID, Product_ID, quantity)
            VALUES (%s, %s, %s)
            """,
            (order_id, product_id, qty_int),
        )
        conn.commit()
        flash("Thêm sản phẩm vào đơn hàng thành công", "success")
    except Exception as e:
        conn.rollback()
        flash(f"Lỗi khi thêm sản phẩm (có thể do trigger kiểm tra stock): {e}", "danger")
    finally:
        cursor.close()
        conn.close()

    return redirect(url_for("order_detail", order_id=order_id))

# ==========================
#  HỆ THỐNG QUẢN LÝ KHÁCH HÀNG
# ==========================

# List customer + filter
@app.route("/customers")
@login_required
def customer_list():
    search = request.args.get("q", "")
    city = request.args.get("city")

    base_sql = """
        SELECT c.Customer_ID,
               u.Username,
               u.Name,
               u.Email,
               u.Street,
               u.City,
               up.Phone_number AS PrimaryPhone
        FROM CUSTOMER c
        JOIN USER u ON u.User_ID = c.Customer_ID
        LEFT JOIN USER_PHONE up
               ON up.User_ID = u.User_ID AND up.Is_primary = TRUE
    """
    conditions = []
    params = []

    if search:
        conditions.append("(u.Name LIKE %s OR u.Email LIKE %s)")
        like = f"%{search}%"
        params.extend([like, like])

    if city:
        conditions.append("u.City = %s")
        params.append(city)

    if conditions:
        base_sql += " WHERE " + " AND ".join(conditions)

    base_sql += " ORDER BY u.Name ASC"

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(base_sql, params)
    customers = cursor.fetchall()

    # Lấy danh sách city cho combobox filter
    cursor.execute(
        """
        SELECT DISTINCT u.City
        FROM CUSTOMER c
        JOIN USER u ON u.User_ID = c.Customer_ID
        WHERE u.City IS NOT NULL
        ORDER BY u.City
        """
    )
    cities = [row["City"] for row in cursor.fetchall()]

    cursor.close()
    conn.close()

    return render_template(
        "customers.html",
        customers=customers,
        cities=cities,
        selected_city=city,
        search=search,
    )


# Xem chi tiết 1 khách hàng (info + thống kê)
@app.route("/customers/<int:customer_id>")
@login_required
def customer_detail(customer_id):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    # Thông tin user
    cursor.execute(
        """
        SELECT c.Customer_ID,
               u.Username,
               u.Name,
               u.Email,
               u.Street,
               u.City
        FROM CUSTOMER c
        JOIN USER u ON u.User_ID = c.Customer_ID
        WHERE c.Customer_ID = %s
        """,
        (customer_id,),
    )
    customer = cursor.fetchone()

    if not customer:
        cursor.close()
        conn.close()
        flash("Không tìm thấy khách hàng", "warning")
        return redirect(url_for("customer_list"))

    # Danh sách phone
    cursor.execute(
        """
        SELECT Phone_number, Phone_type, Is_primary
        FROM USER_PHONE
        WHERE User_ID = %s
        ORDER BY Is_primary DESC, Phone_type
        """,
        (customer_id,),
    )
    phones = cursor.fetchall()

    # Tổng tiền đã chi (function fn_customer_total_spent)
    cursor.execute(
        "SELECT fn_customer_total_spent(%s) AS total_spent",
        (customer_id,),
    )
    total_spent = cursor.fetchone()["total_spent"]

    # Danh sách đơn hàng của customer
    cursor.execute(
        """
        SELECT o.Order_ID, o.Order_date, o.Delivery_date, o.Status, o.Total_cost
        FROM CUSTOMER c
        JOIN OWN ow ON ow.Customer_ID = c.Customer_ID
        JOIN SHOPPING_CART sc ON sc.Cart_ID = ow.Cart_ID
        JOIN ORIGINATES_FROM ofr ON ofr.Cart_ID = sc.Cart_ID
        JOIN SHOPPING_ORDER o ON o.Order_ID = ofr.Order_ID
        WHERE c.Customer_ID = %s
        ORDER BY o.Order_date DESC
        """,
        (customer_id,),
    )
    orders = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template(
        "customer_detail.html",
        customer=customer,
        phones=phones,
        total_spent=total_spent,
        orders=orders,
    )


# Cho phép chỉnh sửa thông tin cơ bản của khách hàng (bảng USER)
@app.route("/customers/<int:customer_id>/edit", methods=["GET", "POST"])
@login_required
def customer_edit(customer_id):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        """
        SELECT c.Customer_ID,
               u.Username,
               u.Name,
               u.Email,
               u.Street,
               u.City
        FROM CUSTOMER c
        JOIN USER u ON u.User_ID = c.Customer_ID
        WHERE c.Customer_ID = %s
        """,
        (customer_id,),
    )
    customer = cursor.fetchone()

    if not customer:
        cursor.close()
        conn.close()
        flash("Không tìm thấy khách hàng", "warning")
        return redirect(url_for("customer_list"))

    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        street = request.form.get("street")
        city = request.form.get("city")

        if not name:
            flash("Name không được để trống", "danger")
            return render_template("customer_form.html", customer=customer)

        try:
            cursor2 = conn.cursor()
            cursor2.execute(
                """
                UPDATE USER
                SET Name = %s,
                    Email = %s,
                    Street = %s,
                    City = %s
                WHERE User_ID = %s
                """,
                (name, email, street, city, customer_id),
            )
            conn.commit()
            cursor2.close()
            flash("Cập nhật thông tin khách hàng thành công", "success")
            return redirect(url_for("customer_detail", customer_id=customer_id))
        except Exception as e:
            conn.rollback()
            flash(f"Lỗi khi cập nhật: {e}", "danger")

    cursor.close()
    conn.close()
    return render_template("customer_form.html", customer=customer)
