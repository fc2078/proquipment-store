# All imports
from flask import Flask, render_template, request, redirect, flash, abort
import pymysql
from dynaconf import Dynaconf
import flask_login

# Declare Flask application
app = Flask(__name__)


# Config settings
conf = Dynaconf(
    settings_file = ["settings.toml"]
)

# Config secret key
app.secret_key = conf.secret_key

# Establish database connection
def connect_db():
    conn = pymysql.connect(
        host = "10.100.34.80",
        database = "fchowdury_proquipment_store",
        user = "fchowdury",
        password = conf.password,
        autocommit = True,
        cursorclass = pymysql.cursors.DictCursor
    )
    return conn


# User Login Manager
login_manager = flask_login.LoginManager()
login_manager.init_app(app)
login_manager.login_view=("/login")


# Classes
class User:
    is_authenticated = True
    is_anonymous = False
    is_active = True

    def __init__(self, user_id, username, email, first_name, last_name):
        self.id = user_id
        self.username = username
        self.email = email
        self.first_name = first_name
        self.last_name = last_name

    def get_id(self):
        return str(self.id)


# Load User Session
@login_manager.user_loader
def load_user(user_id):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute(f"SELECT * FROM `Customer` WHERE `id` = {user_id};")
    result = cursor.fetchone()
    cursor.close()
    conn.close
    if result is not None:
        return User(result["id"], result["username"], result["email"], result["first_name"], result["last_name"])


# Homepage initialization
@app.route("/")
def index():
    return render_template("homepage.html.jinja")


# Browse products
@app.route("/browse")
def product_browse():
    query = request.args.get("query")
    conn = connect_db()
    cursor = conn.cursor()
    if query is None:
        cursor.execute("SELECT * FROM `Product`;")
    else:
        cursor.execute(f"SELECT * FROM `Product` WHERE `name` LIKE '%{query}%' OR `description` LIKE '%{query}%' OR `price` LIKE '%{query}%';")
    results = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template("browse.html.jinja", products = results)


# Separate page per product
@app.route("/product/<product_id>")
def product_page(product_id):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute(f"SELECT * FROM `Product` WHERE `id` = {product_id};")
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    if result is None:
        abort(404)
    return render_template("product.html.jinja", product = result)
        

# Add item to cart
@app.route("/product/<product_id>/cart", methods=["POST"])
@flask_login.login_required
def add_to_cart(product_id):
    quantity = request.form["quantity"]
    customer_id = flask_login.current_user.id
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute(f"""
    INSERT INTO `Cart`
        (`customer_id`, `product_id`, `quantity`)
    VALUES
        ({customer_id}, {product_id}, {quantity})
    ON DUPLICATE KEY UPDATE
        `quantity` = `quantity` + {quantity}
    """)
    cursor.close()
    conn.close()
    return redirect("/cart")


# Sign up page
@app.route("/signup", methods=["POST", "GET"])
def signup_page():
    if flask_login.current_user.is_authenticated:
        return redirect("/")
    if request.method == "POST":
        first_name = request.form["fname"]
        last_name = request.form["lname"]
        email = request.form["email"]
        address = request.form["address"]
        username = request.form["username"]
        password = request.form["pass"]
        confirm_password = request.form["confpass"]
        conn = connect_db()
        cursor = conn.cursor()
        if len(username.strip()) > 20:
            flash("Username must be 20 characters or less.")
        else:
            if len(password.strip()) < 8:
                flash("Password must be 8 characters or longer.")
            else:
                if password != confirm_password:
                    flash("Passwords do not match.")
                else:
                    try:
                        cursor.execute(f"""
                            INSERT INTO `Customer`
                                (`username`, `password`, `first_name`, `last_name`, `email`, `address`)
                            VALUES
                                ('{username}', '{password}', '{first_name}', '{last_name}', '{email}', '{address}');
                        """)
                    except pymysql.err.IntegrityError:
                        flash("Username or email is already in use.")
                    else:
                        return redirect("/login")
                    finally:
                        cursor.close()
                        conn.close()
    return render_template("signup.html.jinja")


# Login Page
@app.route("/login", methods=["POST", "GET"])
def login_page():
    if flask_login.current_user.is_authenticated:
        return redirect("/")
    if request.method == "POST":
        username = request.form["userVer"].strip()
        password = request.form["passVer"]
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute(f"SELECT * FROM `Customer` WHERE `username` = '{username}';")
        result = cursor.fetchone()
        cursor.close()
        conn.close()

        if result is None:
            flash("Your username and/or password is incorrect.")
        
        elif password != result["password"]:
            flash("Your username and/or password is incorrect.")
        
        else:
            user = User(result["id"], result["username"], result["email"], result["first_name"], result["last_name"])

            #Loging In
            flask_login.login_user(user)

            return redirect("/")

    return render_template("login.html.jinja")


# Cart Page
@app.route("/cart", methods=["GET"])
@flask_login.login_required
def cart_page():
    conn = connect_db()
    cursor = conn.cursor()
    customer_id = flask_login.current_user.id
    cursor.execute(f"""
        SELECT
            `name`,
            `price`,
            `Cart`.`quantity`,
            `image`,
            `product_id`,
            `Cart`.`id`
        FROM `Cart` 
        JOIN `Product` on `product_id` = `Product`.`id` 
        WHERE `customer_id` = {customer_id};
    """)
    results = cursor.fetchall()
    total = 0

    if len(results) > 0:
        for item in results:
            total += (item["price"] * item["quantity"])
        total = round(total, 2)
    cursor.close()
    conn.close()
    return render_template("cart.html.jinja", cartContents = results, sum = total)


# Remove item from Cart
@app.route("/cart/remove_cart", methods=["POST"])
@flask_login.login_required
def remove_cart():
    conn = connect_db()

    cursor = conn.cursor()

    customer_id = flask_login.current_user.id

    cart_id = request.form["id"]

    cursor.execute(f"""
    DELETE FROM `Cart`
    WHERE
        `customer_id` = {customer_id}
    AND
        `Cart`.`id` = {cart_id};
    """)

    
    cursor.close()
    conn.close()

    return redirect("/cart")


# Update Item Quantity in Cart
@app.route("/cart/<cart_id>/update", methods=["POST"])
@flask_login.login_required
def update_cart(cart_id):
    conn = connect_db()

    cursor = conn.cursor()

    new_qty = request.form["quantity"]

    cursor.execute(f"""
    UPDATE `Cart`
    SET `quantity` = {new_qty}
    WHERE `id` = {cart_id}
    ;""")

    
    cursor.close()
    conn.close()

    return redirect("/cart")

# Checkout page
@app.route("/checkout", methods=["GET"])
@flask_login.login_required
def checkout():
    conn = connect_db()
    cursor = conn.cursor()
    customer_id = flask_login.current_user.id

    cursor.execute(f"""
        SELECT
            `name`,
            `price`,
            `Cart`.`quantity`,
            `image`,
            `product_id`,
            `Cart`.`id`
        FROM `Cart` 
        JOIN `Product` on `product_id` = `Product`.`id` 
        WHERE `customer_id` = {customer_id};
    """)

    # Fetch cart items
    results = cursor.fetchall()

    if len(results) == 0:
        return redirect("/browse")
    
    else:
        subtotal = 0
        for item in results:
            subtotal += (item["price"] * item["quantity"])
        
        # Calculate taxes (10%) and shipping fees ($5)
        # Insert any tax rate and shipping charge
        tax_rate = 0.10
        shipping_fee = 5.00
        tax = round(subtotal * tax_rate, 2)
        total = round(subtotal + tax + shipping_fee, 2)
    
    # Fetch user info
    cursor.execute(f"""
        SELECT * FROM `Customer`
        WHERE `id` = {customer_id}
    ;""")
    consumer = cursor.fetchone()

    # Close connections
    cursor.close()
    conn.close()

    return render_template(
        "checkout.html.jinja", 
        cartContents=results, 
        subtotal=subtotal, 
        tax=tax, 
        shipping=shipping_fee, 
        total=total, 
        customer=consumer
    )


@app.route("/thankyou")
def thankyou():
    return render_template("thankyou.html.jinja")

# User logout
@app.route("/logout")
def logout():
    flask_login.logout_user()
    return redirect("/")