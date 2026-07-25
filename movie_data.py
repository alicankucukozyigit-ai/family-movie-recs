"""Static genre/mood reference data and TMDB API helpers."""

import os

import requests

TMDB_API_KEY = os.environ.get("TMDB_API_KEY")
TMDB_BASE_URL = "https://api.themoviedb.org/3"

RATING_ORDER = ["G", "PG", "PG-13", "R", "NC-17"]

GENRES = {
    "28": "Action",
    "12": "Adventure",
    "16": "Animation",
    "35": "Comedy",
    "80": "Crime",
    "99": "Documentary",
    "18": "Drama",
    "10751": "Family",
    "14": "Fantasy",
    "36": "History",
    "27": "Horror",
    "10402": "Music",
    "9648": "Mystery",
    "10749": "Romance",
    "878": "Science Fiction",
    "10770": "TV Movie",
    "53": "Thriller",
    "10752": "War",
    "37": "Western",
}

MOODS = {
    "funny": {"label": "Funny", "genres": ["35", "16"]},
    "adventurous": {"label": "Adventurous", "genres": ["12", "28"]},
    "heartwarming": {"label": "Heartwarming", "genres": ["10751", "10749"]},
    "exciting": {"label": "Exciting", "genres": ["28", "53"]},
    "chill": {"label": "Chill", "genres": ["35", "10402"]},
    "classic": {"label": "Family Classic", "genres": ["10751", "16"]},
}


def strictest_rating(ratings):
    """Given a list of rating strings, return the strictest (lowest) one."""
    indices = [RATING_ORDER.index(r) for r in ratings if r in RATING_ORDER]
    if not indices:
        return "PG-13"
    return RATING_ORDER[min(indices)]


def discover_movies(certification_lte, genre_ids, min_rating=None, year_from=None, year_to=None, page=1):
    """Call TMDB discover/movie with an age-rating cap, genre filter, and optional rating/year filters."""
    if not TMDB_API_KEY:
        raise RuntimeError("TMDB_API_KEY is not set")

    params = {
        "api_key": TMDB_API_KEY,
        "certification_country": "US",
        "certification.lte": certification_lte,
        "include_adult": "false",
        "sort_by": "popularity.desc",
        "vote_count.gte": 50,
        "page": page,
    }
    if genre_ids:
        params["with_genres"] = "|".join(genre_ids)
    if min_rating:
        params["vote_average.gte"] = min_rating
    if year_from:
        params["primary_release_date.gte"] = f"{year_from}-01-01"
    if year_to:
        params["primary_release_date.lte"] = f"{year_to}-12-31"

    resp = requests.get(f"{TMDB_BASE_URL}/discover/movie", params=params, timeout=10)
    resp.raise_for_status()
    return resp.json().get("results", [])


def search_movies(query, page=1):
    """Call TMDB search/movie for a free-text title search."""
    if not TMDB_API_KEY:
        raise RuntimeError("TMDB_API_KEY is not set")

    params = {
        "api_key": TMDB_API_KEY,
        "query": query,
        "include_adult": "false",
        "page": page,
    }
    resp = requests.get(f"{TMDB_BASE_URL}/search/movie", params=params, timeout=10)
    resp.raise_for_status()
    return resp.json().get("results", [])


def poster_url(path, size="w342"):
    if not path:
        return None
    return f"https://image.tmdb.org/t/p/{size}{path}"


def score_and_rank(movies, favorite_genre_ids, limit=12):
    """Boost movies that match more of the selected members' favorite genres."""
    fav = set(favorite_genre_ids)

    def score(movie):
        movie_genres = set(str(g) for g in movie.get("genre_ids", []))
        overlap = len(movie_genres & fav)
        return (overlap, movie.get("popularity", 0))

    ranked = sorted(movies, key=score, reverse=True)
    return ranked[:limit]


def compute_genre_weights(members):
    """Blend explicit favorite genres, favorite movies, and rating history into per-genre weights."""
    weights = {}

    def bump(genre_id, amount):
        weights[genre_id] = weights.get(genre_id, 0) + amount

    for member in members:
        for gid in member.genre_id_list():
            bump(gid, 2)
        for fav in member.favorite_movies:
            for gid in fav.genre_id_list():
                bump(gid, 1)
        for rating in member.ratings:
            amount = 1 if rating.thumbs_up else -1
            for gid in rating.genre_id_list():
                bump(gid, amount)

    return weights


def top_genres(weights, limit=4):
    """Pick the highest positive-weight genres to drive a discover query."""
    positive = [(gid, w) for gid, w in weights.items() if w > 0]
    positive.sort(key=lambda pair: pair[1], reverse=True)
    return [gid for gid, _ in positive[:limit]]


def score_by_affinity(movies, genre_weights, disliked_tmdb_ids=None, limit=12):
    """Rank movies by summed genre affinity weight, so disliked genres/movies sink rather than get excluded."""
    disliked_tmdb_ids = disliked_tmdb_ids or set()

    def score(movie):
        movie_genres = [str(g) for g in movie.get("genre_ids", [])]
        weight = sum(genre_weights.get(g, 0) for g in movie_genres)
        if movie.get("id") in disliked_tmdb_ids:
            weight -= 1000
        return (weight, movie.get("popularity", 0))

    ranked = sorted(movies, key=score, reverse=True)
    return ranked[:limit]
