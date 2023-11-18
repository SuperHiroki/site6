import sys
import os
current_directory = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_directory)
from database import db, User, Comment, Movie, Page
from flask import Flask, render_template, redirect, url_for, flash, request
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from datetime import datetime
import pytz
from werkzeug.utils import secure_filename
import uuid

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://site6user:140286TakaHiro@localhost:3306/site6db_3'

db.init_app(app)
with app.app_context():
    db.create_all()

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
migrate = Migrate(app, db)

####################################################
#ログイン
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import hashlib

limiter = Limiter(get_remote_address, app=app, default_limits=["30 per minute"])

login_manager = LoginManager()
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    already_used_or_not="他のサイトで使っている名前やパスワードは絶対に使用しないでください。"
    if request.method=="POST":
        nickname=request.form.get("nickname")
        password=request.form.get("password")
        if User.query.filter_by(nickname=nickname).first():
            already_used_or_not="そのnicknameはすでに使われています"
        else:
            user=User(nickname=nickname)
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            login_user(user)
            return redirect(url_for('home'))
    nickname=get_nickname()
    return render_template("signup.html", nickname=nickname, already_used_or_not=already_used_or_not)

@app.route('/login', methods=['GET', 'POST'])
@limiter.limit("30/minute") 
def login():
    good_or_bad="コメントするにはログインが必要です"
    if request.method=="POST":
        nickname=request.form.get("nickname")
        password=request.form.get("password")
        user=User.query.filter_by(nickname=nickname).first()
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for('home'))
        else:
            good_or_bad="nicknameかpasswordが間違っています"
    nickname=get_nickname()
    return render_template("login.html", nickname=nickname, good_or_bad=good_or_bad)

@app.route('/logout')
def logout():
    if current_user.is_authenticated:
        logout_user()
    return redirect(url_for('home'))

@app.route('/superuser')
def superuser():
    user=User.query.filter_by(nickname="ShiroatoHiro").first()
    login_user(user)
    return redirect(url_for('home'))

####################################################
#メインの関数
def get_nickname():
    if current_user.is_authenticated:
        return current_user.nickname
    else:
        return "ログインしていません"

def def_new_page_true_false():
    if current_user.is_authenticated and current_user.nickname=="ShiroatoHiro":
        return True
    else:
        return False

import html
def escape_text(text):
    return str(html.escape(text)).replace("\n", "<br>")

from flask import Flask, send_from_directory
@app.route('/videos/<path:filename>', methods=['GET'])
def download_file(filename):
    print(filename)
    return send_from_directory(os.path.join(current_directory, 'movies'), filename)

@app.route('/')
def home():
    nickname=get_nickname()
    pages = Page.query.all()
    new_page_true_false=def_new_page_true_false()
    return render_template('home.html', nickname=nickname, pages=pages, new_page_true_false=new_page_true_false)

@app.route('/page/<int:page_id>', methods=['GET', 'POST'])
def view_page(page_id):
    message_for_delete_comment=""
    page_title_explanation_change=""
    upload_movie=""
    delete_movie=""
    if current_user.is_authenticated:
        if "comment" in request.form:
            comment = escape_text(request.form.get("comment"))
            new_comment = Comment(content=comment, time=datetime.now(pytz.timezone('Asia/Tokyo')), page_id=page_id, user_id=current_user.id)
            db.session.add(new_comment)
            db.session.commit()
        elif "delete_comment_id" in request.form:
            delete_comment_id = request.form.get("delete_comment_id")
            delete_comment=Comment.query.get(delete_comment_id) 
            if delete_comment and delete_comment.user_id==current_user.id:
                db.session.delete(delete_comment)
                db.session.commit()
                message_for_delete_comment="コメントID="+delete_comment_id+"を削除しました"
            else:
                message_for_delete_comment="間違えています"
        elif "page_explanation" in request.form:
            page_title = request.form.get("page_title")
            page_explanation = request.form.get("page_explanation")
            page = Page.query.get(page_id)
            page.title=page_title
            page.page_explanation=page_explanation
            db.session.add(page)
            db.session.commit()
        elif 'file' in request.files:
            file = request.files['file']
            filename = secure_filename(file.filename)
            if Movie.query.filter_by(content=filename).first():
                return "同じ名前のファイルがすでにある"
            else:
                file.save(os.path.join(current_directory, 'movies', filename))
                movie_title=request.form.get("movie_title")
                movie_comment=request.form.get("movie_comment")
                movie=Movie(title=movie_title, comment=movie_comment, content=filename, page_id=page_id)
                db.session.add(movie)
                db.session.commit()
        elif 'movie_id_delete' in request.form:
            movie_id_delete=request.form.get("movie_id_delete")
            delete_movie=Movie.query.get(movie_id_delete) 
            if delete_movie:
                db.session.delete(delete_movie)
                db.session.commit()
                delete_movie_name=delete_movie.content
                if os.path.isfile(os.path.join(current_directory, 'movies', delete_movie_name)):
                    os.remove(os.path.join(current_directory, 'movies', delete_movie_name))
                else:
                    print("ファイルが存在しません")
    elif not current_user.is_authenticated and request.method=="POST":
        return redirect(url_for('login'))
    nickname=get_nickname()
    page = Page.query.filter_by(id=page_id).first()
    movies = Movie.query.filter_by(page_id=page_id).all()
    comments = Comment.query.filter_by(page_id=page_id).all()
    nicknames_with_comments = [(User.query.filter_by(id=comment.user_id).first().nickname, comment) for comment in comments]
    if current_user.is_authenticated and current_user.nickname=='ShiroatoHiro':
        with open(os.path.join(current_directory,"page_title_explanation_change.txt"), "r") as f:
                page_title_explanation_change=(f.read()).format(page.title, page.page_explanation)
        with open(os.path.join(current_directory,"upload_movie.txt"), "r") as f:
                upload_movie=(f.read())  
        with open(os.path.join(current_directory,"delete_movie.txt"), "r") as f:
                delete_movie=(f.read())
    movies = Movie.query.filter_by(page_id=page_id).all()
    return render_template('page.html', nickname=nickname, page=page, movies=movies, nicknames_with_comments=nicknames_with_comments, 
                           page_title_explanation_change=page_title_explanation_change, page_explanation=page.page_explanation, message_for_delete_comment=message_for_delete_comment, upload_movie=upload_movie, delete_movie=delete_movie)

@app.route('/page/new', methods=['GET', 'POST'])
def new_page():
    if get_nickname()=="ShiroatoHiro":
        if request.method=="POST":
            title=request.form.get("title")
            page_explanation=request.form.get("page_explanation")
            page=Page(title=title, page_explanation=page_explanation)
            db.session.add(page)
            db.session.commit()
            return redirect(url_for('home'))
        nickname=get_nickname()
        return render_template("new_page.html", nickname=nickname)
    else:
        return "あなたは管理者ではありません"

if __name__=="__main__":
    app.run()
