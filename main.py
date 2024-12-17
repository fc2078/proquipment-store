# All imports
from flask import Flask, render_template, request, redirect, flash
import pymysql
from dynaconf import Dynaconf

# Declare Flash application
app = Flask(__name__)

conf = Dynaconf(
    settings_file = ["settings.toml"]
)

app.secret_key = conf.secret_key

def connect_db():
    """Connect to database"""
    conn = pymysql.connect(
        host = "10.100.34.80",
        database = "fchowdury_proquipment_store",
        user = "fchowdury",
        password = conf.password,
        autocommit = True,
        cursorclass = pymysql.cursors.DictCursor,
    )
    return conn

@app.route("/")
def index():
    return render_template('homepage.html.jinja')

# Browsing page
@app.route("/browse")
def product_browse():
    query = request.args.get('query')
    conn = connect_db()
    cursor = conn.cursor()
    if query is None:
        cursor.execute("SELECT * FROM `product`;")
    else:
        cursor.execute(f"SELECT * FROM `product` WHERE `name` LIKE '%{query}%';")
    results = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template("browse.html.jinja", products = results)

# Products pages
@app.route("/product/<product_id>")
def product_page(product_id):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute(f"SELECT * FROM `product` WHERE `id` = {product_id};")
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    return render_template("product.html.jinja", product = result)

# Signup page
@app.route("/signup", methods=["POST", "GET"])
def signup_page():
    if request.method == "POST":
        first_name = request.form["first_name"]
        last_name = request.form["last_name"]
        email = request.form["email"]
        address = request.form["address"]
        username = request.form["username"]
        password = request.form["password"]
        confirm_password = request.form["confirm_password"]
        conn = connect_db()
        cursor = conn.cursor()
        if password != confirm_password:
            flash("Passwords do not match.")
        try:
            cursor.execute(f"""
                INSERT INTO `customer`
                    (`first_name`, `last_name`, `email`, `address`, `username`, `password`, `confirm_password`)
                VALUES
                    ('{first_name}', '{last_name}', '{email}', '{address}', '{username}', '{password}', '{confirm_password}');
            """)
        except pymysql.err.IntegrityError:
            flash("Sorry, that username or email is already taken. Try another.")
        else:
            return redirect("/signin")
        finally:
            cursor.close()
            conn.close()
    return render_template("signup.html.jinja")