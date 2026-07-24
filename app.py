import os

from flask import Flask, flash, redirect, render_template, request, url_for
from flask_login import (
    LoginManager,
    current_user,
    login_required,
    login_user,
    logout_user,
)

from models import FamilyMember, User, db
from movie_data import (
    GENRES,
    MOODS,
    RATING_ORDER,
    discover_movies,
    poster_url,
    score_and_rank,
    strictest_rating,
)

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-key-change-me")

database_url = os.environ.get("DATABASE_URL", "sqlite:///local.db")
# Render provides postgres:// but SQLAlchemy needs postgresql://
if database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)
app.config["SQLALCHEMY_DATABASE_URI"] = database_url
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


with app.app_context():
    db.create_all()


@app.route("/")
def landing():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))
    return render_template("landing.html")


@app.route("/signup", methods=["GET", "POST"])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        if not email or not password:
            flash("Email and password are required.")
            return render_template("signup.html")
        if User.query.filter_by(email=email).first():
            flash("An account with that email already exists.")
            return render_template("signup.html")
        user = User(email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        login_user(user)
        return redirect(url_for("dashboard"))
    return render_template("signup.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for("dashboard"))
        flash("Invalid email or password.")
    return render_template("login.html")


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("landing"))


@app.route("/dashboard")
@login_required
def dashboard():
    return render_template("dashboard.html", members=current_user.members, genres=GENRES, ratings=RATING_ORDER)


@app.route("/members/add", methods=["POST"])
@login_required
def add_member():
    name = request.form.get("name", "").strip()
    max_rating = request.form.get("max_rating", "PG-13")
    genre_ids = request.form.getlist("genres")
    if not name:
        flash("Name is required.")
        return redirect(url_for("dashboard"))
    if max_rating not in RATING_ORDER:
        max_rating = "PG-13"
    member = FamilyMember(
        user_id=current_user.id,
        name=name,
        max_rating=max_rating,
        favorite_genres=",".join(genre_ids),
    )
    db.session.add(member)
    db.session.commit()
    return redirect(url_for("dashboard"))


@app.route("/members/<int:member_id>/delete", methods=["POST"])
@login_required
def delete_member(member_id):
    member = db.session.get(FamilyMember, member_id)
    if member and member.user_id == current_user.id:
        db.session.delete(member)
        db.session.commit()
    return redirect(url_for("dashboard"))


@app.route("/pick")
@login_required
def pick():
    if not current_user.members:
        flash("Add at least one family member before picking a movie.")
        return redirect(url_for("dashboard"))
    return render_template("pick.html", members=current_user.members, moods=MOODS)


@app.route("/results", methods=["POST"])
@login_required
def results():
    member_ids = request.form.getlist("member_ids")
    mood_key = request.form.get("mood")

    selected = [m for m in current_user.members if str(m.id) in member_ids]
    if not selected:
        flash("Pick at least one family member.")
        return redirect(url_for("pick"))

    mood = MOODS.get(mood_key, MOODS["classic"])

    age_limit = strictest_rating([m.max_rating for m in selected])

    favorite_ids = set()
    for m in selected:
        favorite_ids.update(m.genre_id_list())

    try:
        raw_movies = discover_movies(certification_lte=age_limit, genre_ids=mood["genres"])
    except RuntimeError:
        flash("Movie search isn't configured yet — missing TMDB_API_KEY.")
        return redirect(url_for("pick"))
    except Exception:
        flash("Couldn't reach the movie database right now. Please try again.")
        return redirect(url_for("pick"))

    ranked = score_and_rank(raw_movies, favorite_ids)
    movies = [
        {
            "title": m.get("title"),
            "overview": m.get("overview"),
            "rating": m.get("vote_average"),
            "poster": poster_url(m.get("poster_path")),
        }
        for m in ranked
    ]

    return render_template(
        "results.html",
        movies=movies,
        age_limit=age_limit,
        mood_label=mood["label"],
        selected_names=[m.name for m in selected],
    )


if __name__ == "__main__":
    app.run(debug=True, port=5001)
