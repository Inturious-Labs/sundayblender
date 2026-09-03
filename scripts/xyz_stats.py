#!/usr/bin/env python3
"""Print The Sunday Blender's Xiaoyuzhou subscriber count and per-episode plays.

Scrapes the public podcast page. Xiaoyuzhou has no developer API; the page is
Next.js and embeds its data as JSON in a <script id="__NEXT_DATA__"> tag.

Usage: scripts/xyz_stats.py [--json]
"""
import json
import re
import sys
import urllib.request

PID = "691d248b88967822c085fda5"
URL = f"https://www.xiaoyuzhoufm.com/podcast/{PID}"
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/128 Safari/537.36"


def fetch():
    req = urllib.request.Request(URL, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=20) as r:
        html = r.read().decode("utf-8")
    m = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>', html, re.S)
    if not m:
        sys.exit("could not find __NEXT_DATA__ on the page; Xiaoyuzhou may have changed its markup")
    return json.loads(m.group(1))["props"]["pageProps"]["podcast"]


def main():
    p = fetch()
    if "--json" in sys.argv:
        out = {
            "subscribers": p["subscriptionCount"],
            "episodes": p["episodeCount"],
            "total_play_seconds": p["playTime"],
            "recent": [
                {"title": e["title"], "plays": e["playCount"], "favorites": e["favoriteCount"],
                 "comments": e["commentCount"], "published": e["pubDate"]}
                for e in p["episodes"]
            ],
        }
        print(json.dumps(out, ensure_ascii=False, indent=2))
        return
    print(f"Subscribers: {p['subscriptionCount']}")
    print(f"Episodes:    {p['episodeCount']}")
    print(f"Play time:   {p['playTime'] // 3600}h {p['playTime'] % 3600 // 60}m (all episodes)")
    print()
    print(f"{'plays':>6} {'fav':>4} {'published':<12} title")
    for e in p["episodes"]:
        print(f"{e['playCount']:>6} {e['favoriteCount']:>4} {e['pubDate'][:10]:<12} {e['title']}")


if __name__ == "__main__":
    main()
