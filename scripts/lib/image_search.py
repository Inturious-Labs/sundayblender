"""
Image candidate search for The Sunday Blender.

Finds image candidates for a story by querying, in order of preference:
  1. Brave Image Search  (fresh news photos; needs BRAVE_API_KEY)
  2. Wikimedia Commons   (license-clean; free, no key)
  3. Openverse           (license-clean; free, no key)

Brave is the only source that reliably has *this week's* news photos, which is
most of what TSB covers. Commons and Openverse are the license-clean fallbacks
for evergreen subjects (people, places, animals, artworks).

Deliberately zero pip dependencies — HTTP goes through curl via subprocess, the
same way fetch_image.sh does it. See memory: tsb-image-picker-arch.
"""

import json
import os
import re
import subprocess
import threading
import time
from dataclasses import dataclass, asdict
from typing import List, Optional

# Brave's free tier allows roughly one request per second and answers 429 to
# anything faster. The picker prefetches every story in parallel, so calls are
# funnelled through this gate rather than being fired at once.
_BRAVE_MIN_INTERVAL = 1.15
_brave_gate = threading.Lock()
_brave_last = [0.0]


def _brave_throttle():
    with _brave_gate:
        wait = _BRAVE_MIN_INTERVAL - (time.monotonic() - _brave_last[0])
        if wait > 0:
            time.sleep(wait)
        _brave_last[0] = time.monotonic()

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")

# Brave returns 240x240 thumbnails among its results; they are unusable at
# newsletter width, so anything narrower than this is dropped before display.
MIN_WIDTH = 600

# Stock libraries that serve visibly watermarked comps to non-subscribers. The
# file downloads fine and looks right in a thumbnail, so the watermark is only
# discovered after it is placed -- flag these in the UI instead.
WATERMARK_HOSTS = (
    "plus.unsplash.com", "gettyimages", "shutterstock", "istockphoto",
    "alamy", "dreamstime", "123rf", "depositphotos", "stock.adobe",
    "agefotostock", "imago-images", "profimedia", "zumapress",
)


def _watermark_risk(url: str, site: str) -> bool:
    hay = f"{url} {site}".lower()
    return any(h in hay for h in WATERMARK_HOSTS)

# Stopwords for query building. These are the words that survive in every story
# and carry no search signal.
_STOP = {
    "the", "a", "an", "and", "or", "but", "of", "in", "on", "at", "to", "for",
    "with", "from", "by", "as", "is", "was", "were", "are", "be", "been", "it",
    "its", "his", "her", "their", "they", "he", "she", "that", "this", "these",
    "those", "there", "then", "than", "so", "if", "when", "while", "after",
    "before", "about", "into", "over", "under", "out", "up", "down", "not",
    "no", "one", "two", "three", "first", "last", "new", "most", "more", "some",
    "who", "which", "what", "how", "all", "can", "could", "would", "has", "had",
    "have", "will", "said", "says", "year", "years", "day", "days", "week",
    "people", "made", "make", "took", "take", "went", "get", "got",
    # Common in TSB prose but useless as image search terms: units, vague
    # quantities, and narrative connectives.
    "where", "every", "times", "time", "second", "seconds", "minute", "minutes",
    "hour", "hours", "metre", "metres", "meter", "meters", "kilometre",
    "kilometres", "kilometer", "kilometers", "mile", "miles", "million",
    "billion", "thousand", "hundred", "percent", "cent", "since", "until",
    "another", "other", "others", "again", "still", "just", "also", "much",
    "many", "each", "same", "than", "them", "were", "been", "being", "because",
    "through", "during", "between", "against", "without", "within", "around",
    "back", "down", "only", "even", "ever", "never", "very", "well", "like",
    "long", "little", "large", "small", "high", "low", "next", "later",
    "early", "began", "begin", "started", "start", "called", "known", "left",
    "right", "came", "come", "given", "give", "found", "find", "think",
    "thought", "want", "wanted", "need", "needed", "used", "using", "work",
    "worked", "working", "world", "place", "thing", "things", "part", "parts",
    "number", "numbers", "point", "points", "line", "lines", "away", "along",
    "across", "behind", "before", "after", "above", "below", "under", "over",
}


@dataclass
class Candidate:
    """One image candidate offered to the editor."""
    url: str            # direct full-size image URL (what we download)
    thumb: str          # thumbnail URL for the contact sheet
    width: int
    height: int
    source: str         # "brave" | "commons" | "openverse"
    site: str           # origin domain, shown under the thumbnail
    title: str = ""
    license: str = ""   # populated for commons/openverse
    watermark: bool = False  # likely a watermarked stock comp

    def to_dict(self):
        return asdict(self)


def _curl_json(url: str, headers: Optional[dict] = None, timeout: int = 25,
               with_status: bool = False):
    """GET a URL and parse JSON. Returns None on any failure — callers treat a
    dead source as 'no candidates' rather than an error, so one flaky API
    never breaks the picker.

    With with_status=True, returns (data, http_status) so callers can tell a
    rate-limit (429) apart from a genuine empty result and retry.
    """
    cmd = ["curl", "-s", "-m", str(timeout), "-A", UA, "-L"]
    if with_status:
        cmd += ["-w", "\n%{http_code}"]
    for k, v in (headers or {}).items():
        cmd += ["-H", f"{k}: {v}"]
    cmd.append(url)
    try:
        out = subprocess.run(cmd, capture_output=True,
                             timeout=timeout + 5).stdout.decode("utf-8", "replace")
    except subprocess.TimeoutExpired:
        return (None, 0) if with_status else None

    status = 0
    if with_status:
        body, _, tail = out.rpartition("\n")
        try:
            status = int(tail.strip())
        except ValueError:
            body = out
        out = body

    try:
        data = json.loads(out) if out.strip() else None
    except (json.JSONDecodeError, ValueError):
        data = None
    return (data, status) if with_status else data


def _quote(s: str) -> str:
    from urllib.parse import quote
    return quote(s, safe="")


# --- query building ---------------------------------------------------------

def build_query(story_text: str, section: str = "") -> str:
    """Turn a story paragraph into an image search query.

    TSB drafts bold every proper noun, which is exactly the signal we need, so
    a heuristic beats a generic keyword extractor here and costs nothing. An
    LLM was considered and rejected: the bolded entities already are the query.
    """
    text = story_text

    # A leading [Cycling]/[Snooker] tag marks the sport — strong signal.
    tag = ""
    m = re.match(r"^\s*\[([^\]]+)\]", text)
    if m:
        tag = m.group(1).strip()
        text = text[m.end():]

    # Bolded entities, in document order, de-duplicated.
    bolds = re.findall(r"\*\*(.+?)\*\*", text)
    seen, entities = set(), []
    for b in bolds:
        b = re.sub(r"[^\w\s:'’\-]", " ", b).strip()
        b = re.sub(r"\s+", " ", b)
        key = b.lower()
        if b and key not in seen and len(b) > 1:
            seen.add(key)
            entities.append(b)

    parts = entities[:3]

    # Drop an entity that merely repeats one already chosen ("Yayoi Kusama"
    # bolded twice, or "Black Myth: Wukong" then "Black Myth: Zhong Kui").
    pruned = []
    for p in parts:
        pl = p.lower()
        if any(pl in q.lower() or q.lower() in pl for q in pruned):
            continue
        pruned.append(p)
    parts = pruned

    # If the story bolds little or nothing, fall back to salient capitalised
    # words plus frequent nouns from the opening sentences.
    if len(parts) < 2:
        plain = re.sub(r"[*`\[\]]", "", text)
        caps = re.findall(r"\b([A-Z][a-z]{2,})\b", plain[:400])
        for c in caps:
            cl = c.lower()
            # Skip anything already covered by a chosen entity, so a story that
            # bolds "Yayoi Kusama" does not also collect "Yayoi" and "Kusama".
            if cl in _STOP or cl in seen:
                continue
            if any(cl in p.lower() for p in parts):
                continue
            seen.add(cl)
            parts.append(c)
            if len(parts) >= 3:
                break

    if len(parts) < 2:
        plain = re.sub(r"[*`\[\]]", "", text).lower()
        words = [w for w in re.findall(r"[a-z]{4,}", plain)
                 if w not in _STOP and w not in seen]
        freq = {}
        for w in words:
            freq[w] = freq.get(w, 0) + 1
        for w, _ in sorted(freq.items(), key=lambda kv: -kv[1])[:3]:
            parts.append(w)

    if tag:
        parts.append(tag)

    # Entity names alone say who, not what. Add the story's most distinctive
    # topical nouns so "Nepal Tibet" becomes "Nepal Tibet landslide glacier" --
    # without this, a search returns generic scenery of the right place.
    chosen = " ".join(parts).lower()
    # Strip bolded spans first: those words are already represented by the
    # entities, and leaving them in lets the entity name win on frequency.
    plain = re.sub(r"\*\*.+?\*\*", " ", text)
    plain = re.sub(r"[*`\[\]]", "", plain).lower()

    counts = {}
    for w in re.findall(r"[a-z]{4,}", plain):
        if w in _STOP or w in chosen:
            continue
        counts[w] = counts.get(w, 0) + 1

    # Repetition marks the subject: a word the story returns to is what the
    # story is about. Require >=2 mentions, then prefer the longer word as a
    # tiebreak, since longer nouns are more specific than short ones.
    topical = [w for w, n in sorted(counts.items(), key=lambda kv: (-kv[1], -len(kv[0])))
               if n >= 2][:2]

    query = " ".join(parts[:4] + topical)
    return re.sub(r"\s+", " ", query).strip()


# --- sources ----------------------------------------------------------------

def search_brave(query: str, count: int = 12, offset: int = 0) -> List[Candidate]:
    """Brave Image Search. Returns direct file URLs plus proxied thumbnails.

    Note: the image endpoint has no freshness/date parameter (web search does),
    so recency has to be carried in the query text itself.
    """
    key = os.environ.get("BRAVE_API_KEY")
    if not key:
        return []

    url = (f"https://api.search.brave.com/res/v1/images/search"
           f"?q={_quote(query)}&count={count}&safesearch=strict&country=ALL")
    headers = {"Accept": "application/json", "X-Subscription-Token": key}

    # Free tier is ~1 req/s. Throttle, then back off on a 429 — without this a
    # parallel prefetch silently loses most stories to rate limiting.
    data = None
    for attempt in range(4):
        _brave_throttle()
        data, status = _curl_json(url, headers=headers, with_status=True)
        if status == 429:
            time.sleep(1.5 * (attempt + 1))
            continue
        break

    if not data or "results" not in data:
        return []

    out = []
    for r in data.get("results", []):
        props = r.get("properties") or {}
        direct = props.get("url")
        if not direct:
            continue
        thumb = (r.get("thumbnail") or {}).get("src") or direct
        w = int(props.get("width") or r.get("width") or 0)
        h = int(props.get("height") or r.get("height") or 0)
        site = (r.get("meta_url") or {}).get("hostname") or r.get("source") or ""
        out.append(Candidate(
            url=direct, thumb=thumb, width=w, height=h,
            source="brave", site=site, title=(r.get("title") or "")[:120],
        ))
    return out


def search_commons(query: str, count: int = 8) -> List[Candidate]:
    """Wikimedia Commons. License-clean, free, no key."""
    url = ("https://commons.wikimedia.org/w/api.php"
           f"?action=query&generator=search&gsrsearch={_quote(query)}"
           f"&gsrnamespace=6&gsrlimit={count}"
           "&prop=imageinfo&iiprop=url|size|extmetadata&iiurlwidth=800&format=json")
    data = _curl_json(url)
    if not data:
        return []

    out = []
    for page in (data.get("query", {}).get("pages", {}) or {}).values():
        info = (page.get("imageinfo") or [{}])[0]
        direct = info.get("url")
        if not direct:
            continue
        meta = info.get("extmetadata") or {}
        lic = (meta.get("LicenseShortName") or {}).get("value", "")
        out.append(Candidate(
            url=direct,
            thumb=info.get("thumburl") or direct,
            width=int(info.get("width") or 0),
            height=int(info.get("height") or 0),
            source="commons",
            site="commons.wikimedia.org",
            title=page.get("title", "").replace("File:", "")[:120],
            license=lic,
        ))
    return out


def search_openverse(query: str, count: int = 8) -> List[Candidate]:
    """Openverse. License-clean aggregator, free, no key required."""
    url = (f"https://api.openverse.org/v1/images/?q={_quote(query)}"
           f"&page_size={count}&license_type=all")
    data = _curl_json(url)
    if not data:
        return []

    out = []
    for r in data.get("results", []) or []:
        direct = r.get("url")
        if not direct:
            continue
        out.append(Candidate(
            url=direct,
            thumb=r.get("thumbnail") or direct,
            width=int(r.get("width") or 0),
            height=int(r.get("height") or 0),
            source="openverse",
            site=r.get("source") or r.get("provider") or "",
            title=(r.get("title") or "")[:120],
            license=r.get("license") or "",
        ))
    return out


def wikipedia_lead_image(term: str) -> List[Candidate]:
    """The lead image of a Wikipedia article.

    Resolves a named person or place far more reliably than keyword search --
    'Tadej Pogacar' gets the right portrait instead of a crowd shot.
    """
    url = (f"https://en.wikipedia.org/api/rest_v1/page/summary/{_quote(term)}"
           "?redirect=true")
    data = _curl_json(url, timeout=15)
    if not data:
        return []
    orig = data.get("originalimage") or {}
    src = orig.get("source")
    if not src:
        return []
    return [Candidate(
        url=src,
        thumb=(data.get("thumbnail") or {}).get("source") or src,
        width=int(orig.get("width") or 0),
        height=int(orig.get("height") or 0),
        source="commons",
        site="wikipedia.org",
        title=data.get("title", "")[:120],
        license="see Commons",
    )]


# --- aggregation ------------------------------------------------------------

def _dedupe(cands: List[Candidate]) -> List[Candidate]:
    seen, out = set(), []
    for c in cands:
        key = re.sub(r"^https?://", "", c.url.split("?")[0]).lower()
        if key in seen:
            continue
        seen.add(key)
        out.append(c)
    return out


def find_candidates(query: str, limit: int = 3, offset: int = 0,
                    sources: Optional[List[str]] = None,
                    lead_term: Optional[str] = None) -> List[Candidate]:
    """Gather candidates for a query across the enabled sources.

    Brave leads because it has the fresh news photos; Commons and Openverse
    fill in behind it. Results below MIN_WIDTH are dropped -- they cannot fill
    the newsletter column.
    """
    sources = sources or ["brave", "commons", "openverse"]
    pool: List[Candidate] = []

    if lead_term and "commons" in sources and offset == 0:
        pool += wikipedia_lead_image(lead_term)
    if "brave" in sources:
        pool += search_brave(query, count=max(20, limit * 4))
    if "commons" in sources:
        pool += search_commons(query, count=8)
    if "openverse" in sources:
        pool += search_openverse(query, count=8)

    pool = [c for c in pool if c.width == 0 or c.width >= MIN_WIDTH]
    pool = _dedupe(pool)
    for c in pool:
        c.watermark = _watermark_risk(c.url, c.site)

    # Landscape suits the newsletter column better than tall portraits.
    def rank(c: Candidate):
        landscape = 0 if (c.height and c.width / max(c.height, 1) >= 1.2) else 1
        return (1 if c.watermark else 0, landscape, -(c.width or 0))

    pool.sort(key=rank)

    # Interleave by source rather than returning a straight ranking. Brave wins
    # on resolution nearly every time, so a pure sort would bury the
    # license-clean Commons/Openverse hits and hide that choice from the editor.
    by_source = {}
    for c in pool:
        by_source.setdefault(c.source, []).append(c)

    ordered, order = [], ["brave", "commons", "openverse"]
    used_sites = {}
    deferred = []
    while any(by_source.get(s) for s in order):
        for s in order:
            bucket = by_source.get(s)
            if not bucket:
                continue
            c = bucket.pop(0)
            # Three shots from the same site are usually near-identical and
            # waste the editor's three slots; hold repeats back as filler.
            n = used_sites.get(c.site, 0)
            if c.site and n >= 1:
                deferred.append(c)
            else:
                used_sites[c.site] = n + 1
                ordered.append(c)

    ordered += deferred
    return ordered[offset:offset + limit]
