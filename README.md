# Family Movie Night

Weekend-MVP web app that helps a family agree on what to watch: parents create
an account, add profiles for each family member (age rating limit + favorite
genres), then pick who's watching tonight plus a mood, and get an
age-appropriate, taste-matched shortlist from TMDB.

## Local setup

```bash
cd family-movie-recs
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # then fill in TMDB_API_KEY
export $(cat .env | xargs)
python app.py
```

App runs at http://localhost:5001

Get a free TMDB API key (v3 auth) at https://www.themoviedb.org/settings/api
after creating an account.

## Deployment (Render)

1. Push this repo to GitHub.
2. In Render: New > Blueprint, point at the repo to create the web service
   (`render.yaml` defines build/start commands).
3. Separately, create a Postgres database: New > PostgreSQL (Free plan).
   Copy its **Internal Database URL**.
4. In the web service's Environment tab, set `DATABASE_URL` to that URL and
   `TMDB_API_KEY` to your TMDB key — neither is committed anywhere.
5. Push to `main` auto-deploys.

**Important**: `DATABASE_URL` is intentionally `sync: false` in `render.yaml`
and the file does *not* declare a `databases:` block. Render's Blueprint
sync re-links any `fromDatabase`-bound env var on every deploy, which
previously caused it to silently swap `DATABASE_URL` to a different,
freshly-empty database on a later sync — wiping all user data without
warning. Keep it manually set in the dashboard; don't reintroduce a
`fromDatabase` binding for it.

## Status

MVP scope: email/password accounts, per-member age rating + favorite genres,
mood picker, TMDB-backed recommendations. No streaming availability,
watchlists, rating history, or social login in v1.
