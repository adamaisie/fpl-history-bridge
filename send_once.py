import os, json, urllib.request
from app import report
data = report()
message = {"from":"onboarding@resend.dev","to":["adamzfeldman@gmail.com"],"subject":"Your FPL team GW"+str(data["gameweek"]),"html":"<h2>FPL players</h2>"+"".join("<p>"+p["name"]+" ("+str(p["points"])+" pts)</p>" for p in data["players"])}
req=urllib.request.Request("https://api.resend.com/emails",data=json.dumps(message).encode(),headers={"Authorization":"Bearer "+os.environ["RESEND_API_KEY"],"Content-Type":"application/json"})
print(urllib.request.urlopen(req,timeout=30).read().decode())
