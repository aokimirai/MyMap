import os, json
from flask import Flask, flash, redirect, render_template, request, session
from flask_session.__init__ import Session
from werkzeug.security import check_password_hash, generate_password_hash
from helpers import apology, login_required
import werkzeug
from datetime import datetime
import sqlite3
# from flask_sqlalchemy import SQLAlchemy
import re
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

def db(ope):
    con = sqlite3.connect('./mymap.db')
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
            return redirect("/home")
    except:
        return render_template("index.html")