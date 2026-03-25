from flask import Flask, jsonify, request
from flask_cors import CORS
import aiohttp
import asyncio
import os
from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__)
CORS(app)

async def fetch_ban(uid):
    url = f"http://raw.thug4ff.xyz/check_ban/{uid}/great"
    timeout = aiohttp.ClientTimeout(total=10)
    try:
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(url) as res:
                data = await res.json()
                if data.get("status") == 200 and data.get("data"):
                    return data["data"]
    except Exception as e:
        print(f"[ban] error: {e}")
    return None

async def fetch_info(uid, region):
    url = f"https://ff-info.thug4ff.xyz/player-info/{region}/{uid}"
    timeout = aiohttp.ClientTimeout(total=10)
    try:
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(url) as res:
                return await res.json()
    except Exception as e:
        print(f"[info] error: {e}")
    return None

async def gather_data(uid, region):
    ban, info = await asyncio.gather(
        fetch_ban(uid),
        fetch_info(uid, region),
        return_exceptions=True
    )
    if isinstance(ban, Exception): ban = None
    if isinstance(info, Exception): info = None
    return ban, info

@app.route("/api/player")
def player():
    uid = request.args.get("uid", "").strip()
    region = request.args.get("region", "ind").strip().lower()

    if not uid.isdigit():
        return jsonify({"error": "Invalid UID"}), 400

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    ban, info = loop.run_until_complete(gather_data(uid, region))
    loop.close()

    if not ban and not info:
        return jsonify({"error": "Player not found"}), 404

    basic  = info.get("basicInfo", info.get("player", {})) if info else {}
    guild  = info.get("clanBasicInfo", info.get("guild", {})) if info else {}
    pet    = info.get("petInfo", {}) if info else {}
    social = info.get("socialInfo", {}) if info else {}

    period = ban.get("period") if ban else None
    period_str = f"{period}+ months" if isinstance(period, int) else str(period) if period else "N/A"

    return jsonify({
        "uid":        uid,
        "region":     region.upper(),
        "nickname":   (ban or {}).get("nickname") or basic.get("nickname") or "Unknown",
        "is_banned":  int((ban or {}).get("is_banned", 0)),
        "ban_period": period_str,
        "level":      basic.get("level", "N/A"),
        "exp":        basic.get("exp", "N/A"),
        "likes":      basic.get("liked") or basic.get("likes") or "N/A",
        "bp_badges":  basic.get("badgeCnt") or basic.get("badges") or "N/A",
        "br_rank":    basic.get("rankingPoints") or basic.get("rank_point") or "N/A",
        "cs_rank":    basic.get("csRankingPoints") or basic.get("cs_rank") or "N/A",
        "guild_name": guild.get("clanName") or guild.get("name") or "No Guild",
        "guild_level":   guild.get("clanLevel") or guild.get("level") or "N/A",
        "guild_members": guild.get("memberNum") or guild.get("members") or "N/A",
        "pet_name":   pet.get("name", "N/A"),
        "pet_level":  pet.get("level", "N/A"),
        "signature":  social.get("signature") or basic.get("signature") or "—",
    })

@app.route("/")
def home():
    return "Free Fire Player Info API is running!"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
