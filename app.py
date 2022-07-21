import os
from flask import Flask
from flask import render_template
from flask import request, flash, redirect
from flask import url_for, session
from werkzeug.utils import secure_filename
import sqlite3

app = Flask(__name__)
app.secret_key="12345678"
app.config['IMAGE_UPLOAD_FOLDER'] = 'static/imgs'
IMG_EXTENSIONS = set(['jpeg', 'jpg', 'png'])

db_con = sqlite3.connect("cookbook.db")
db_con.execute("create table if not exists users(userid text primary key, mail text, password text)")
db_con.execute("create table if not exists recipes(id integer primary key, rname text, image text, cooktime text, temp text, ratings text, ingredians text, steps text, author text, price text)")
db_con.execute("create table if not exists cart(userid text, id integer, foreign key(userid) references users(userid), foreign key(id) references recipes(id), unique(userid, id))")
db_con.close()

def check_file_extension(file):
    return '.' in file and file.rsplit('.', 1)[1] in IMG_EXTENSIONS

@app.route('/')
def index_page():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login_user():
    if request.method == 'POST':
        userid = request.form['userid']
        password = request.form['password']
        db_con = sqlite3.connect("cookbook.db")
        db_con.row_factory=sqlite3.Row
        db_cur=db_con.cursor()
        db_cur.execute("select * from users where userid=? and password=?", (userid, password))
        data = db_cur.fetchone()
        if data:
            session['userid'] = data['userid']
            session['mail'] = data['mail']
            session['loggedIn'] = True
            return redirect(url_for("cookbook"))
        else:
            flash("Username or Password incorrect", "danger")
    return redirect(url_for("index_page"))

@app.route('/register', methods=['GET','POST'])
def register_user():
    if request.method == "POST":
        try:
            userid = request.form['userid']
            mail = request.form['mail']
            password = request.form['password']
            db_con = sqlite3.connect("cookbook.db")
            db_cur = db_con.cursor()
            db_cur.execute("insert into users(userid, mail, password)values(?,?,?)",(userid, mail, password))
            db_con.commit()
            flash("User registered successfully", "success")
        except:
            flash("Error while registering user", "danger")
        finally:
            db_con.close()
            return redirect(url_for("index_page"))
    return render_template('register.html')

@app.route('/logout')
def logout_user():
    session.clear()
    return redirect(url_for('index_page'))

@app.route('/addToCart', methods=['GET', 'POST'])
def add_to_cart():
    if request.method == 'POST':
        id = request.form['id']
        db_con = sqlite3.connect("cookbook.db")
        db_cur = db_con.cursor()
        try:
            db_cur.execute("insert into cart(userid, id)values(?,?)",(session['userid'], id))
            db_con.commit()
        except:
            db_con.rollback()
        db_con.close()
    return redirect(url_for('cookbook'))

@app.route('/removeFromCart', methods=['GET', 'POST'])
def remove_from_cart():
    if request.method == 'POST':
        id = request.form['id']
        db_con = sqlite3.connect("cookbook.db")
        db_cur = db_con.cursor()
        try:
            db_cur.execute("delete from cart where userid=? and id=?", (session['userid'], id))
            db_con.commit()
        except:
            db_con.rollback()
        db_con.close()
    return redirect(url_for('cart'))

@app.route('/cart', methods=['GET', 'POST'])
def cart():
    db_con = sqlite3.connect("cookbook.db")
    db_cur = db_con.cursor()
    db_cur.execute("select * from cart")
    data = db_cur.fetchall()
    retdata = []
    for i in range(len(data)):
        db_cur.execute("select * from recipes where id=?", (data[i][1], ))
        retdata.append(db_cur.fetchone())
    db_con.close()
    amount = 0
    for i in range(len(retdata)):
        amount += int(retdata[i][9])
    return render_template("cart.html", data=retdata, amount=amount)

@app.route('/cookbook', methods=['GET', 'POST'])
def cookbook():
    db_con = sqlite3.connect("cookbook.db")
    db_cur = db_con.cursor()
    db_cur.execute("select * from recipes")
    data = db_cur.fetchall()
    db_con.close()
    return render_template("cookbook.html", recipes=data)

@app.route('/searchRecipes', methods=['GET', 'POST'])
def search_recipes():
    if request.method == 'POST':
        searchtype = request.form['searchtype']
        search = request.form['search']
        db_con = sqlite3.connect("cookbook.db")
        db_cur = db_con.cursor()
        if searchtype == "ratings":
            db_cur.execute("select * from recipes where ratings > {0}".format(int(search)))
        else:
            db_cur.execute("select * from recipes where {0} like '%{1}%'".format(searchtype, search))
        data =  db_cur.fetchall()
        db_con.close()
        return render_template("search.html", data=data)
    return render_template("search.html", data=None)

@app.route('/addRecipe', methods=['GET', 'POST'])
def add_recipe():
    if request.method == 'POST':
        rname = request.form['rname']
        cooktime = request.form['cooktime']
        temp = request.form['temp']
        ratings = request.form['ratings']
        ingredians = request.form['ingredians']
        steps = request.form['steps']
        price = request.form['price']
        author = session['userid']
        image = request.files['image']
        if image and check_file_extension(image.filename):
            upload_name = secure_filename(image.filename)
            image.save(os.path.join(app.config['IMAGE_UPLOAD_FOLDER'], upload_name))
        final_img_name = upload_name
        db_con = sqlite3.connect("cookbook.db")
        try:
            db_cur = db_con.cursor()
            db_cur.execute("insert into recipes(rname, image, cooktime, temp, ratings, ingredians, steps, author, price)values(?, ?, ?, ?, ?, ?, ?, ?, ?)", (rname, final_img_name, cooktime, temp, ratings, ingredians, steps, author, price))
            db_con.commit()
            flash("Recipe Added successfully", "success")
        except:
            flash("Error occured while adding recipe", "danger")
            db_con.rollback()
        db_con.close()
        return redirect(url_for("cookbook"))
    return render_template('add.html')

def getApp():
    return app

if __name__ == "__main__":
    app.run(debug=True)
