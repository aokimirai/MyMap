import os, json
from flask import Flask, flash, redirect, render_template, render_template_string, request, session, jsonify
from flask_session.__init__ import Session
from werkzeug.security import check_password_hash, generate_password_hash
from helpers import apology, login_required
import werkzeug
from datetime import datetime
import sqlite3
import re
import sys
from flask_wtf.csrf import CSRFProtect


app = Flask(__name__, static_folder='upload')


csrf = CSRFProtect(app)

app.config["TEMPLATES_AUTO_RELOAD"] = True


# ファイルシステムを使用するようにセッションを構成します (署名付き Cookie の代わりに)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# csrf対策
with open("securet.txt") as f:
    securet = f.read()
securetkey = securet
app.config['WTF_CSRF_SECRET_KEY'] = securetkey
app.config['WTF_CSRF_ENABLED'] = True

# 画像のアップロード
UPLOAD_POST_FOLDER = './upload'
ALLOWED_EXTENSIONS = set(['.jpg','.gif','.png','image/gif','image/jpeg','image/png'])
app.config['UPLOAD_FOLDER'] = UPLOAD_POST_FOLDER
DBNAME = './mymap.db'

def db(ope):
    con = sqlite3.connect(DBNAME)
    db = con.cursor()
    db = db.execute(ope)
    con.close()
    return db

def password_check(password):
    if len(password) >= 6 and (re.search('[A-Z]', password) or re.search('[a-z]', password)) and re.search('[0-9]', password):
        return True
    return False

@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/")
def index():
    try:
        if session["user_id"]:
            return redirect("/mypage")
    except:
        return render_template("index.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    session.clear()
    username = request.form.get("username")
    password = request.form.get("password")
    if request.method == "POST":
        if not username:
            return apology("ユーザーネームを入力してください", 403)
        elif not password:
            return apology("パスワードを入力してください", 403)

        con = sqlite3.connect(DBNAME)
        db = con.cursor()
        db.execute("SELECT * FROM users WHERE username = ?", (username,))
        users = db.fetchone()
        con.close()
        if users != None:
            if check_password_hash(users[2], password):
                session["user_id"] = users[0]
                flash("ログインしました")
                return redirect("/")
            else:
                return apology("パスワードが無効です", 403)
        else:
            return apology("ユーザネームが無効です", 403)

    else:
        return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        if not username:
            return apology("ユーザーネームを入力してください", 400)
        con = sqlite3.connect(DBNAME)
        db = con.cursor()
        db.execute("SELECT * FROM users where username=?", (username,))
        user = db.fetchone()
        if user != None:
            return apology("このユーザーネームは既に使われています", 400)
        elif not password:
            return apology("パスワードを入力してください", 400)
        elif password_check(password) == False:
            return apology("英数字を一文字以上含んだ6文字以上のパスワードを入力してください")
        elif password != request.form.get("confirmation"):
            return apology("パスワードが一致しません", 400)
        password = generate_password_hash(password)
        db.execute("INSERT INTO users (username, hash) VALUES(?, ?)", (username, password))
        con.commit()
        con.close()
        flash("登録が完了しました")
        return redirect("/login")
    else:
        return render_template("register.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

@app.route("/mypage", methods=["GET", "POST"])
def mypage():
    if request.method == "POST":
        action = request.form.get('action')
        # postid = request.form.get("postid")
        if action == "rewrite":
            con = sqlite3.connect(DBNAME)
            db = con.cursor()
            # posts = db.execute("SELECT * FROM posts WHERE id = ?",(postid,)).fetchall()
            con.close()
            return render_template("repost.html") #,posts=posts
        elif action == "del":
            con = sqlite3.connect(DBNAME)
            db = con.cursor()
            db.execute("DELETE FROM posts WHERE id = ?",(postid,))
            con.commit()
            con.close()
            return redirect("/mypage")
        else:
            return redirect("/mypage")
    else:
        userid = session["user_id"]
        con = sqlite3.connect(DBNAME)
        db = con.cursor()
        users = db.execute("SELECT display_name,icon,created_at FROM users WHERE id = ?", (userid,)).fetchall()
        markers = db.execute("SELECT lat,lng,comment,cate,created_at FROM markers WHERE userid = (?)", (userid,)).fetchall()
        con.close()
        return render_template("mypage.html",users=users, markers=markers)


@app.route("/set", methods=["GET", "POST"])
def set():
    if request.method == "POST":
        userid = session["user_id"]
        nickname = request.form.get("nickname")
        con = sqlite3.connect(DBNAME)
        db = con.cursor()
        users = db.execute("SELECT icon FROM users WHERE id = ?",(userid,)).fetchone()
        if users[0] == None:
            filepath=None
        else:
            filepath=db.execute("SELECT icon FROM users WHERE id = ?",(userid,)).fetchall()[0][0]

        img = request.files['imgfile']
        if img:
            filepath = datetime.now().strftime("%Y%m%d_%H%M%S_") \
            + werkzeug.utils.secure_filename(img.filename)
            img.save(os.path.join(app.config['UPLOAD_FOLDER'] + '/iconimg', filepath))
        
        db.execute("UPDATE users SET display_name=?, icon=? WHERE id=?",(nickname,filepath,userid,))
        con.commit()
        con.close()
        return redirect("/mypage")
    else:
        userid = session["user_id"]
        con = sqlite3.connect(DBNAME)
        db = con.cursor()
        users = db.execute("SELECT display_name,icon FROM users WHERE id = (?)", (userid,)).fetchall()
        return render_template("set.html",users=users)

@csrf.exempt
@app.route("/map", methods=["GET", "POST"])
def map():
    if request.method == "POST":
        userid = session["user_id"]
        lat = request.json['lat']
        lng = request.json['lng']
        comment = request.json['text']
        con = sqlite3.connect(DBNAME)
        db = con.cursor()
        db.execute("INSERT INTO markers (userid,lat,lng,comment) VALUES (?,?,?,?)", (userid,lat,lng,comment,))
        con.commit()
        markers = db.execute("SELECT lat,lng,comment,cate,created_at FROM markers WHERE userid = (?) ORDER BY created_at DESC", (userid,)).fetchone()
        con.close()
        print(markers)
        dict = {'lat':markers[0],
                'lng':markers[1],
                'text':markers[2],
                'cate':markers[3],
                'time':markers[4]
                }
        return jsonify(dict)
    else:
        userid = session["user_id"]
        con = sqlite3.connect(DBNAME)
        db = con.cursor()
        markers = db.execute("SELECT lat,lng,comment,cate,created_at FROM markers WHERE userid = (?) ORDER BY created_at DESC", (userid,)).fetchall()
        newmarker = db.execute("SELECT lat,lng FROM markers WHERE userid = (?) ORDER BY created_at DESC", (userid,)).fetchone()
        con.close()
        return render_template("map.html", markers = markers, newmarker = newmarker)
    
@app.route("/dell", methods=["POST"])
def dell():
    userid = session["user_id"]
    lat = request.json['lat']
    lng = request.json['lng']
    con = sqlite3.connect(DBNAME)
    db = con.cursor()
    db.execute("DELETE FROM markers WHERE lat = ? and lng = ?",(lat, lng))
    con.commit()
    con.close()
    return redirect("/map")