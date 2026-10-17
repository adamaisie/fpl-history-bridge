import os, json, urllib.request, urllib.error, html
from datetime import datetime, timezone
from app import report

TO = os.getenv("FPL_RECIPIENT", "adamzfeldman@gmail.com")
FROM = os.getenv("FPL_FROM") or "onboarding@resend.dev"
API_KEY = os.environ.get("RESEND_API_KEY")
if not API_KEY:
    raise RuntimeError("RESEND_API_KEY missing. Configure GitHub Actions repository secret.")

data = report()
gw = data["gameweek"]
players = data["players"]
starters = sorted((p for p in players if p["multiplier"] > 0), key=lambda p: -p["counted_points"])
bench = sorted((p for p in players if p["multiplier"] == 0), key=lambda p: -p["points"])
def number(n):
    return f"{float(n):.2f}"
def block(p, on_bench=False):
    n = html.escape(p["name"]) + (" (C)" if p["captain"] else "")
    pts = int(p["points"] if on_bench else p["counted_points"])
    minutes = int(p["minutes"])
    if p["is_goalkeeper"]:
        stats = f'{minutes} min · <b>{int(p["saves"])} saves</b> · <b>xGC {number(p["expected_goals_conceded"])}</b>'
    elif p["is_defender"]:
        stats = f'{minutes} min · {int(p["goals"])}G/{int(p["assists"])}A · xG {number(p["expected_goals"])} · xA {number(p["expected_assists"])}<br><b>xGC {number(p["expected_goals_conceded"])}</b> · <b>DefCon {int(p["defcon"])}</b>'
    else:
        stats = f'{minutes} min · {int(p["goals"])}G/{int(p["assists"])}A · <b>xG {number(p["expected_goals"])}</b> · <b>xA {number(p["expected_assists"])}</b>'
    f = p.get("next_fixture")
    fixture = (f'{html.escape(f["opponent"] or "?")} ({"H" if f["home"] else "A"}) · FDR {f["difficulty"]}' if f else 'No future fixture listed')
    return f'<div style="padding:10px 0;border-bottom:1px solid #e5e7eb"><div style="font-size:16px"><b>{n}</b> <b style="float:right">{pts} pts</b></div><div style="margin-top:4px">{stats}</div><div style="color:#526070">Next: {fixture}</div></div>'
best = max(starters, key=lambda p:p["counted_points"])
content = f'<div style="font-family:Arial,sans-serif;max-width:560px;margin:auto;color:#17212b;font-size:14px;line-height:1.45"><h2>FPL Weekly Review · GW{gw}</h2><div style="font-size:32px;font-weight:700">{data["team_points"]} pts</div><div style="color:#596575;margin-bottom:16px">Total gameweek score · Team {data["entry_id"]}</div><p>Top scorer: {html.escape(best["name"])} ({int(best["counted_points"])} pts). Underlying numbers and next fixtures below.</p><h3>Starting XI</h3>'+''.join(block(p) for p in starters)+'<h3>Bench · actual player points</h3>'+''.join(block(p, True) for p in bench)+'</div>'
payload = {"from":FROM,"to":[TO],"subject":f"FPL GW{gw} — weekly squad review","html":content}
req = urllib.request.Request("https://api.resend.com/emails",data=json.dumps(payload).encode(),headers={"Authorization":"Bearer "+API_KEY,"Content-Type":"application/json"},method="POST")
try:
    with urllib.request.urlopen(req,timeout=30) as response:
        print("EMAIL_SENT "+response.read().decode())
except urllib.error.HTTPError as e:
    print("EMAIL_SEND_FAILED "+str(e.code)+" "+e.read().decode())
    raise
