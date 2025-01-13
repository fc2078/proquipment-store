from flask import request, redirect, render_template
import pymysql
import flask_login

def connect_db():
    return pymysql.connect(
        host="your_db_host",
        user="your_db_user",
        password="your_db_password",
        database="your_db_name",
        cursorclass=pymysql.cursors.DictCursor
    )

# Route to Display Product Page with Reviews
@app.route("/product/product_id>", methods=["GET"])
def product_page(product_id):
    conn = connect_db()
    cursor = conn.cursor()

    # Fetch product details
    cursor.execute("SELECT * FROM Product WHERE id = %s", (product_id,))
    product = cursor.fetchone()

    # Fetch reviews for the product
    cursor.execute("""
        SELECT r.content, r.created_at, c.first_name AS user_name
        FROM Review r
        JOIN Customer c ON r.customer_id = c.id
        WHERE r.product_id = %s
        ORDER BY r.created_at DESC
    """, (product_id,))
    reviews = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template("product.html.jinja", product=product, reviews=reviews)

# Route to Handle Adding a Review
@app.route("/product/<int:product_id>/review", methods=["POST"])
@flask_login.login_required
def add_review(product_id):
    review_content = request.form.get("review_content")
    customer_id = flask_login.current_user.id

    conn = connect_db()
    cursor = conn.cursor()

    # Insert review into the database
    cursor.execute("""
        INSERT INTO Review (product_id, customer_id, content, created_at)
        VALUES (%s, %s, %s, NOW())
    """, (product_id, customer_id, review_content))
    conn.commit()

    cursor.close()
    conn.close()

    return redirect(f"/product/{product_id}")
