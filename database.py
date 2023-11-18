from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class Page(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(128), nullable=False)
    page_explanation = db.Column(db.String(4096), nullable=False)
    movies = db.relationship('Movie', backref='page', lazy=True)
    comments = db.relationship('Comment', backref='page', lazy=True)

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(1024), nullable=False)
    time = db.Column(db.DateTime, nullable=False)
    page_id = db.Column(db.Integer, db.ForeignKey('page.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

class Movie(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(128), nullable=False)
    comment = db.Column(db.String(1024), nullable=False)
    content = db.Column(db.String(128), nullable=False)
    page_id = db.Column(db.Integer, db.ForeignKey('page.id'), nullable=False)

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nickname = db.Column(db.String(128), unique=True, nullable=False)
    hashed_password = db.Column(db.String(128), nullable=False)
    comments = db.relationship('Comment', backref='user', lazy=True)

    def set_password(self, password):
        self.hashed_password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.hashed_password, password)
