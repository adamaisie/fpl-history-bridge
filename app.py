import json, os, time, urllib.request, urllib.error
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs

BASE = "https://fantasy.premierleague.com/api/"
ENTRY = int(os.environ.get("FPL_ENTRY_ID", "3363511"))
CACHE = {}

def fetch(path, ttl=600):
    now = time.time()
    if path in CACHE and now - CACHE[path][0] < ttl:
        return CACHE[path][1]
    request = urllib.request.Request(BASE + path, headers={"User-Agent": "Mozilla/5.0", "Accept": "application/json"})
    with urllib.request.urlopen(request, timeout=25) as response:
        data = json.load(response)
    CACHE[path] = (now, data)
    return data

def report(gw=None):
    bootstrap = fetch("bootstrap-static/", 900)
    completed = [e["id"] for e in bootstrap["events"] if e.get("finished")]
    if not completed:
        raise ValueError("No completed gameweeks")
    gw = int(gw) if gw is not None else max(completed)
    if gw not in completed:
        raise ValueError("Requested gameweek is not completed")
    picks = fetch(f"entry/{ENTRY}/event/{gw}/picks/", 1800)
    players = {p["id"]: p for p in bootstrap["elements"]}
    teams = {t["id"]: t["short_name"] for t in bootstrap["teams"]}
    output = []
    for pick in picks["picks"]:
        player = players[pick["element"]]
        history = fetch(f"element-summary/{player['id']}/", 3600)["history"]
        rows = [r for r in history if r.get("round") == gw]
        def metric(name):
            return sum(float(r.get(name, 0) or 0) for r in rows)
        output.append({
            "name": player["web_name"], "team": teams.get(player["team"]),
            "player_id": player["id"], "position": pick["position"],
            "captain": pick["is_captain"], "vice_captain": pick["is_vice_captain"],
            "multiplier": pick["multiplier"], "matches": len(rows),
            "opponents": [teams.get(r.get("opponent_team")) for r in rows],
            "minutes": metric("minutes"), "points": metric("total_points"),
            "counted_points": metric("total_points") * pick["multiplier"],
            "goals": metric("goals_scored"), "assists": metric("assists"),
            "clean_sheets": metric("clean_sheets"), "bonus": metric("bonus"),
            "expected_goals": metric("expected_goals"),
            "expected_assists": metric("expected_assists")
        })
    return {"entry_id": ENTRY, "gameweek": gw, "team_points": picks.get("entry_history", {}).get("points"), "players": output}

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        url = urlparse(self.path)
        try:
            if url.path == "/health":
                data = {"status": "ok", "entry_id": ENTRY}
            elif url.path == "/report":
                data = report(parse_qs(url.query).get("gw", [None])[0])
            else:
                self.send_error(404, "Use /health or /report?gw=6")
                return
            status = 200
        except ValueError as exc:
            status, data = 400, {"error": str(exc)}
        except Exception as exc:
            status, data = 502, {"error": str(exc)}
        body = json.dumps(data).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Cache-Control", "public, max-age=300")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

if __name__ == "__main__":
    ThreadingHTTPServer(("0.0.0.0", int(os.environ.get("PORT", "8080"))), Handler).serve_forever()
