from fastapi import FastAPI, Query
from starlette.responses import RedirectResponse
import requests
import time
import os
import json
import threading
from fastapi.middleware.cors import CORSMiddleware

# Create FastAPI app
app = FastAPI()

# Shared clan leaderboard storage (file-based JSON)
CLAN_TOTALS_PATH = os.path.join(os.path.dirname(__file__), "clan_totals.json")
CLAN_TOTALS_LOCK = threading.Lock()

# Make "SWORD_SECRET"
secret = os.environ.get("SWORD_SECRET")
if not secret:
    raise EnvironmentError("SWORD_SECRET environment variable not set.")

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
    return {
        "status": "ok",
        "endpoints": [
            "/stats/fetch",
            "/games/fetch",
            "/profile/search",
            "/profile/getPublicUserInfo/{username}",
            "/profile/clanMembers",
            "/clans/leaderboard"
        ]
    }


# ---------- Players Stats ----------
@app.post("/stats/fetch")
def fetch_stats(timeRange: str = Query("all"), sortBy: str = Query("xp")):
    timestamp_ms = int(time.time() * 1000)
    url = "https://api.swordbattle.io/stats/fetch"
    payload = {
        "sortBy": sortBy,
        "timeRange": timeRange,
        "limit": 100,
        "secret": secret
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
        "secret": secret
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
        "secret": secret
    }
    response = requests.post(url, params={"_": timestamp_ms}, json=payload)
    return response.json()

@app.get("/profile/search")
def search_profile_get(q: str = Query(""), limit: int = Query(25)): 
    return search_profile(q, limit)

@app.post("/profile/getPublicUserInfo/{username}")
def get_public_profile(username: str):
    timestamp_ms = int(time.time() * 1000)
    url = f"https://api.swordbattle.io/profile/getPublicUserInfo/{username}"
    response = requests.post(url, params={"_": timestamp_ms})
    return response.json()

@app.get("/profile/getPublicUserInfo/{username}")
def get_public_profile_get(username: str):
    return get_public_profile(username)

@app.get("/profile/clanMembers")
def get_clan_members(clan: str = Query(...)):
    url = "https://api.swordbattle.io/profile/clanMembers"
    print("Clan Request:", clan)
    response = requests.get(
        url,
        params={
            "clan": clan
        },
        json={"clan": clan}
    )

    data = response.json()

    members = [sanitize_member(m) for m in data.get("members", [])]
    if members:
        update_clan_totals(clan, members)

    return {
        "count": data.get("count", len(members)),
        "xp": data.get("xp"),
        "members": members
    }


@app.get("/clans/leaderboard")
def get_clan_leaderboard():
    with CLAN_TOTALS_LOCK:
        return {"clans": read_clan_totals()}


def read_clan_totals():
    if not os.path.exists(CLAN_TOTALS_PATH):
        return {}
    try:
        with open(CLAN_TOTALS_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except (OSError, json.JSONDecodeError) as err:
        print("Failed to read clan totals:", err)
        return {}


def write_clan_totals(data):
    tmp_path = f"{CLAN_TOTALS_PATH}.tmp"
    try:
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, sort_keys=True)
        os.replace(tmp_path, CLAN_TOTALS_PATH)
    except OSError as err:
        print("Failed to write clan totals:", err)


def update_clan_totals(clan_name, members):
    clan_key = (clan_name or "").strip().lower()
    if not clan_key:
        return

    total_xp = sum((m.get("xp") or 0) for m in members)
    total_playtime = sum((m.get("playtime") or 0) for m in members)
    member_count = len(members)

    with CLAN_TOTALS_LOCK:
        data = read_clan_totals()
        data[clan_key] = {
            "name": clan_name,
            "xp": total_xp,
            "playtime": total_playtime,
            "members": member_count,
            "updated_at": int(time.time())
        }
        write_clan_totals(data)




def sanitize_member(m):
    return {
        "id": m["id"],
        "username": m["username"],
        "clan": m["clan"],
        "xp": m["xp"],
        "playtime": m.get("playtime", 0),
        "mastery": m["mastery"],
        "gems": m["gems"],
        "subscription": m["subscription"],
        "profile_views": m["profile_views"],
        "tags": m.get("tags", {}),
        "skins": {
            "equipped": m["skins"]["equipped"]
        }
    }
