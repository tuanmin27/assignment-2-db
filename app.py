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
