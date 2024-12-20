# All imports
from flask import Flask, render_template, request, redirect, flash, abort
import pymysql
from dynaconf import Dynaconf
import flask_login as login

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
    if result is None:
        abort(404)
    cursor.close()
    conn.close()
    return render_template("product.html.jinja", product = result)



# Signup page
@app.route("/signup", methods=["POST", "GET"])
def signup_page():
    if login.current_user.is_authenticated():
        return redirect("/")
    else:
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
                return redirect("/login")
            finally:
                cursor.close()
                conn.close()
    return render_template("signup.html.jinja")

# Login manager
login_manager = login.LoginManager()
login_manager.init_app(app)
login_manager.login_view = "/login"


# User class
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

@login_manager.user_loader
def load_user(user_id):
    conn = connect_db()
    
    cursor = conn.cursor()

    cursor.execute(f"SELECT * FROM `Customer` WHERE `id` = {user_id};")

    result = cursor.fetchone()
    
    ##Close Connections
    cursor.close()
    conn.close

    if result is not None:
        return User(result["id"], result["username"], result["email"], result["first_name"], result["last_name"])

@app.route("/login", methods=["POST", "GET"])
def login_page():
    if login.current_user.is_authenticated():
        return redirect("/")
    else:
        if request.method == "POST":
            username = request.form["userVer"].strip()
            password = request.form["passVer"]

            conn = connect_db()

            cursor = conn.cursor()

            cursor.execute(f"SELECT * FROM `Customer` WHERE `username` = '{username}';")
            
            result = cursor.fetchone()

            if result is None:
                flash("Your username and/or password is incorrect.")
            
            elif password != result["password"]:
                flash("Your username and/or password is incorrect.")
            
            else:
                user = User(result["id"], result["username"], result["email"], result["first_name"], result["last_name"])

                #Loging In
                login.login_user(user)

                return redirect("/")

    return render_template("login.html.jinja")

@app.route("/product/<product_id>/cart", methods=["POST"])
@login.login_required
def add_to_cart(product_id):
    """Customer adds product to cart. Login is REQUIRED."""
    # get quantity from form
    quantity = request.form["quantity"]

    # check if quantity is a number
    if not quantity.isdigit():
        abort(400)

    # check if quantity is positive
    if int(quantity) <= 0:
        abort(400)

    # check if product exists
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute(f"SELECT * FROM `product` WHERE `id` = {product_id};")

    result = cursor.fetchone()

    if result is None:
        abort(404)

    # check if customer has enough stock
    if result["quantity"] < int(quantity):
        abort(400)

    # get customer id
    customer_id = login.current_user.get_id()

    # add data to database
    cursor.execute(f"""
        INSERT INTO `cart`
            (`customer_id`, `product_id`, `quantity`)
        VALUES
            ({customer_id}, {product_id}, {quantity});
    """)

    # update product quantity
    cursor.execute(f"UPDATE `product` SET `quantity` = `quantity` - {quantity} WHERE `id` = {product_id};")

    # commit changes
    conn.commit()

    cursor.close()
    conn.close()

    return redirect("/cart.html.jinja")

    # redirect user to cart page
    




@app.route("/cart")
@login.login_required
def cart():
    return "This is your cart! Add items you want and proceed with payment and shipping!"

@app.route("/logout")
def logout():
    login.logout_user()
    return redirect("/")