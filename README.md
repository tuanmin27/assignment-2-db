# ECommerceApp – Hướng dẫn kết nối DB & chạy hệ thống

Ứng dụng web demo cho **Assignment 2 – Database**, viết bằng **Python Flask** kết nối **MySQL**.  
Hệ thống hiện tại gồm:

- **Admin site (Web shop / quản trị)**:
  - Login/Logout bằng user DB (`sManager`)
  - Quản lý sản phẩm (Products)
  - Quản lý khách hàng (Customers)
  - Quản lý đơn hàng (Orders)
  - Báo cáo top sản phẩm (Reports – gọi Stored Procedure)

---
2. Chuẩn bị database MySQL
2.1. Import schema + data (Part 1 & Part 2)

Mở MySQL Workbench.

Kết nối bằng tài khoản root (hoặc tài khoản quản trị MySQL của bạn).

Chạy 2 file script:

SOURCE assignment2_part1_script.sql;
SOURCE assignment2_part2_script.sql;


Chọn database:

USE ECommerceDB_Final_Part1;
SHOW TABLES;
SELECT * FROM PRODUCT;


Nếu thấy bảng (PRODUCT, SHOPPING_ORDER, ORDER_ITEM, CUSTOMER, USER, …) và có dữ liệu mẫu → OK.

2.2. Tạo user sManager để app dùng

Đề bài yêu cầu dùng user riêng để kết nối DB.
Trong MySQL Workbench (đang login bằng root):

CREATE USER 'sManager'@'localhost' IDENTIFIED BY '123456';

GRANT SELECT, INSERT, UPDATE, DELETE, EXECUTE
ON ECommerceDB_Final_Part1.*
TO 'sManager'@'localhost';

FLUSH PRIVILEGES;


Bạn có thể đổi mật khẩu, nhưng nhớ cập nhật lại trong file db.py (xem mục 4).

3. Lấy source & cấu trúc project

Nếu source ở GitHub:

git clone https://github.com/<your-username>/<your-repo>.git
cd <your-repo>/ECommerceApp


Cấu trúc cơ bản:

ECommerceApp/
│ app.py              # Flask app (routes, UI logic)
│ db.py               # Kết nối MySQL
│ test_db.py          # Script test kết nối DB
│ requirements.txt    # Danh sách package Python
│ .gitignore
└─templates/
   │ base.html
   │ login.html
   │ products.html
   │ product_form.html
   │ orders.html
   │ order_form.html
   │ order_detail.html
   │ customers.html
   │ customer_detail.html
   │ customer_form.html
   │ report_top_products.html

4. Cấu hình kết nối database (db.py)

File db.py là nơi cấu hình thông tin kết nối MySQL.

Ví dụ:

import mysql.connector

DB_CONFIG = {
    "host": "localhost",
    "database": "ECommerceDB_Final_Part1",  # đúng tên DB đã import
    "user": "sManager",                     # user MySQL đã tạo
    "password": "123456",                   # mật khẩu đúng với MySQL
}

def get_connection():
    return mysql.connector.connect(**DB_CONFIG)


Giải thích:

host: localhost nếu MySQL chạy trên máy hiện tại.

database: đúng tên schema trong MySQL (ECommerceDB_Final_Part1).

user / password: trùng với user đã tạo ở bước 2.2 (sManager / 123456).

Nếu bạn dùng user khác (ví dụ root) thì chỉ cần đổi user và password cho khớp.

5. Cài Flask & thư viện Python

Trong thư mục ECommerceApp, tạo virtual environment:

# tạo venv
python -m venv .venv

# Windows:
.venv\Scripts\activate
# Linux/Mac:
source .venv/bin/activate


Cài các thư viện cần thiết:

pip install -r requirements.txt
# hoặc, nếu không có file requirements.txt:
# pip install flask mysql-connector-python

6. Chạy thử test_db.py để kiểm tra kết nối DB

Mục đích: đảm bảo db.py + MySQL đều OK trước khi chạy web.

Trong thư mục ECommerceApp (venv đã bật):

python test_db.py


Nếu mọi thứ đúng, bạn sẽ thấy log dạng:

Kết nối MySQL thành công!
Số lượng sản phẩm trong PRODUCT: 5


Một số lỗi thường gặp:

Access denied for user 'xxx'@'localhost'
→ Sai user hoặc password trong db.py, hoặc user chưa được GRANT quyền trên DB.

Unknown database 'ECommerceDB_Final_Part1'
→ Chưa chạy script SQL hoặc gõ sai tên database.

Sửa lại db.py hoặc script DB rồi chạy lại python test_db.py cho đến khi thành công.

7. Chạy toàn bộ hệ thống Flask

Khi test_db.py đã OK, bạn có thể chạy web app:

# vẫn trong thư mục ECommerceApp, venv đã bật
flask --app app run


Flask sẽ log ra:

 * Serving Flask app 'app'
 * Running on http://127.0.0.1:5000


Lưu ý:

Không tắt cửa sổ terminal này.

Nhấn Ctrl + C để dừng server khi không dùng nữa.

Nếu muốn bật debug (tự reload khi sửa code):

flask --app app run --debug
