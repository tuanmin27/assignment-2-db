from db import get_connection

def main():
    try:
        conn = get_connection()
        print("Kết nối MySQL thành công!")
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM PRODUCT;")
        count = cursor.fetchone()[0]
        print("Số lượng sản phẩm trong PRODUCT:", count)
    except Exception as e:
        print("Lỗi khi kết nối / query:", e)
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals() and conn.is_connected():
            conn.close()

if __name__ == "__main__":
    main()
