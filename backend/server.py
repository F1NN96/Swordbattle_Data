from fastapi import FastAPI, Query
from starlette.responses import RedirectResponse
import requests
import time
import os
from fastapi.middleware.cors import CORSMiddleware

# Create FastAPI app
app = FastAPI()

# Allow frontend to access this API (CORS)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # can restrict to your frontend URL if needed
    allow_methods=["*"],
    allow_headers=["*"],
)

# Root route for testing
@app.get("/")
def root():
    return RedirectResponse("/stats/fetch")


# ---------- Players Stats ----------
@app.post("/stats/fetch")
def fetch_stats(timeRange: str = Query("all"), sortBy: str = Query("xp")):
    timestamp_ms = int(time.time() * 1000)
    url = "https://api.swordbattle.io/stats/fetch"
    payload = {
        "sortBy": sortBy,
        "timeRange": timeRange,
        "limit": 100,
        "secret": os.environ.get("SWORD_SECRET")
    }
    response = requests.post(url, params={"_": timestamp_ms}, json=payload)
    return response.json()

@app.get("/stats/fetch")
def fetch_stats_get(timeRange: str = Query("all"), sortBy: str = Query("xp")):
    return fetch_stats(timeRange, sortBy)

# ---------- Games Stats ----------
@app.post("/games/fetch")
def fetch_games(timeRange: str = Query("all")):
    timestamp_ms = int(time.time() * 1000)
    url = "https://api.swordbattle.io/games/fetch"
    payload = {
        "sortBy": "coins",
        "timeRange": timeRange,
        "limit": 500,
        "secret": os.environ.get("SWORD_SECRET")
    }
    response = requests.post(url, params={"_": timestamp_ms}, json=payload)
    return response.json()

@app.get("/games/fetch")
def fetch_games_get(timeRange: str = Query("all")):
    return fetch_games(timeRange)


# ---------- Profile Search ----------
@app.post("/profile/search")
def search_profile(q: str = Query(""), limit: int = Query(25)):
    timestamp_ms = int(time.time() * 1000)
    url = "https://api.swordbattle.io/profile/search"
    payload = {
        "q": q,
        "limit": limit,
        "secret": os.environ.get("SWORD_SECRET")
    }
    response = requests.post(url, params={"_": timestamp_ms}, json=payload)
    return response.json()

@app.get("/profile/search")
def search_profile_get(q: str = Query(""), limit: int = Query(25)): 
    return search_profile(q, limit)