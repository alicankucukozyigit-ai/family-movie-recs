from datetime import datetime

from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import check_password_hash, generate_password_hash

db = SQLAlchemy()

RATING_ORDER = ["G", "PG", "PG-13", "R", "NC-17"]


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    members = db.relationship(
        "FamilyMember", backref="user", cascade="all, delete-orphan", order_by="FamilyMember.id"
    )

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class FamilyMember(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    name = db.Column(db.String(80), nullable=False)
    max_rating = db.Column(db.String(10), nullable=False, default="PG-13")
    # Comma-separated TMDB genre IDs, e.g. "35,16,10751"
    favorite_genres = db.Column(db.String(255), nullable=False, default="")

    favorite_movies = db.relationship(
        "FavoriteMovie", backref="member", cascade="all, delete-orphan", order_by="FavoriteMovie.id"
    )

    def genre_id_list(self):
        return [g for g in self.favorite_genres.split(",") if g]


class FavoriteMovie(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    member_id = db.Column(db.Integer, db.ForeignKey("family_member.id"), nullable=False)
    tmdb_id = db.Column(db.Integer, nullable=False)
    title = db.Column(db.String(255), nullable=False)
    poster_path = db.Column(db.String(255), nullable=True)
    # Comma-separated TMDB genre IDs, captured from the search result at add-time
    genre_ids = db.Column(db.String(255), nullable=False, default="")

    def genre_id_list(self):
        return [g for g in self.genre_ids.split(",") if g]
