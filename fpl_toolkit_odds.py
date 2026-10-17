"""Experimental FPL Toolkit public-page odds extractor. Never blocks production email."""
import json
import re
import urllib.request
from html.parser import HTMLParser

URL = "https://www.fpltoolkit.co.uk/match-odds"

class Text(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []
    def handle_data(self, data):
        value = " ".join(data.split())
        if value:
            self.parts.append(value)

def retrieve():
    request = urllib.request.Request(URL, headers={"User-Agent": "Mozilla/5.0 (compatible; FPLPersonalReport/1.0)", "Accept": "text/html"})
    with urllib.request.urlopen(request, timeout=25) as response:
        page = response.read().decode("utf-8", errors="replace")
    parser = Text()
    parser.feed(page)
    return page, parser.parts

def probe():
    page, parts = retrieve()
    text = " ".join(parts)
    # This is a source-availability probe, not yet a validated player matcher.
    indicators = {
        "has_clean_sheet_market": bool(re.search(r"clean.sheet", text, re.I)),
        "has_score_or_assist_market": bool(re.search(r"score.or.assist", text, re.I)),
        "has_percentages": bool(re.search(r"\\d{1,3}%", text)),
        "page_bytes": len(page),
        "visible_text_items": len(parts),
    }
    print(json.dumps(indicators, indent=2))
    if not all(indicators[k] for k in ("has_clean_sheet_market", "has_score_or_assist_market", "has_percentages")):
        raise RuntimeError("FPL Toolkit page does not expose the required markets in fetched HTML")
    return indicators

if __name__ == "__main__":
    probe()
