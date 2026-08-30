#!/usr/bin/env python3
"""
tsb-image-picker — pick images for a Sunday Blender issue from a local contact sheet.

Prefetches image candidates for every story in an issue, then serves a small
local page where you flip through stories and click the one you want. The pick
is downloaded, normalized (JPEG, <=1200px, <=500KB via fetch_image.sh), saved
into the issue folder, and inserted into index.md — then it advances to the
next story.

Usage:
    tsb-image-picker --issue 0829
    tsb-image-picker --issue 20260829 --port 8420
    tsb-image-picker --issue 0829 --no-prefetch    # search lazily instead

Requires BRAVE_API_KEY in the environment (see ~/.secrets) — Brave is the only
source, because TSB needs photographs of this week's events rather than archive
material.

Zero pip dependencies by design — stdlib http.server plus curl/ImageMagick,
matching the rest of scripts/. See memory: tsb-image-picker-arch.
"""

import argparse
import json
import os
import re
import subprocess
import sys
import threading
import webbrowser
from concurrent.futures import ThreadPoolExecutor
from datetime import date
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse, parse_qs

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
sys.path.insert(0, str(SCRIPT_DIR))

from lib.image_search import build_query, find_candidates, Candidate  # noqa: E402

FETCH_IMAGE = SCRIPT_DIR / "fetch_image.sh"
CANDIDATES_PER_STORY = 3


# --- issue + story model ----------------------------------------------------

def resolve_issue_dir(issue: str) -> Path:
    """Accept YYYYMMDD or MMDD (current year), mirroring fetch_image.sh."""
    if re.fullmatch(r"\d{8}", issue):
        year, mmdd = issue[:4], issue[4:]
    elif re.fullmatch(r"\d{4}", issue):
        year, mmdd = str(date.today().year), issue
    else:
        raise SystemExit(f"--issue must be YYYYMMDD or MMDD (got '{issue}')")
    d = REPO_ROOT / "content" / "posts" / year / mmdd
    if not d.is_dir():
        raise SystemExit(f"Issue folder does not exist: {d}")
    return d


def split_frontmatter(text: str):
    """Return (frontmatter_with_delimiters, body). Avoids a yaml dependency —
    Homebrew python3 has no PyYAML while /usr/bin/python3 does, and the picker
    must not care which interpreter starts it."""
    if text.startswith("---"):
        end = text.find("\n---", 3)
        if end != -1:
            cut = text.find("\n", end + 1) + 1
            return text[:cut], text[cut:]
    return "", text


# Sections that never get a story image.
EXCLUDED = {"Editor's Words", "Previous Issues", "Funny", "Subscribe"}


def parse_stories(md_path: Path):
    """Extract image-eligible story paragraphs with their line positions.

    Parses positions directly rather than reusing lib/article_parser.py: that
    parser returns text only, and inserting images needs to know exactly which
    line each story ends on.
    """
    raw = md_path.read_text(encoding="utf-8")
    fm, body = split_frontmatter(raw)
    fm_lines = fm.count("\n")
    lines = body.split("\n")

    stories, section = [], ""
    for i, line in enumerate(lines):
        s = line.strip()
        if s.startswith("## "):
            section = s[3:].strip()
            continue
        if s.startswith("#") or not s or s == "---":
            continue
        if section in EXCLUDED or not section:
            continue
        # Skip lines that are already an image, or Q/A joke lines.
        if s.startswith("![") or re.match(r"^[QA]:", s):
            continue
        # A story is a substantial prose paragraph.
        if len(s) < 200:
            continue

        # An existing image sits above the paragraph (see insert_image).
        existing = None
        for j in range(i - 1, max(i - 4, -1), -1):
            s2 = lines[j].strip()
            if not s2:
                continue
            m = re.match(r"^!\[[^\]]*\]\(([^)]+)\)", s2)
            if m:
                existing = m.group(1)
            break

        stories.append({
            "order": len(stories),
            "section": section,
            "text": s,
            "line": fm_lines + i,   # absolute line index in the full file
            "image": existing,
        })
    return stories


def slugify(name: str, maxlen: int = 10) -> str:
    """Match fetch_image.sh's slug rules: lowercase, alnum/_/-, <=10 chars."""
    s = re.sub(r"[^a-z0-9_-]", "", name.lower().replace(" ", "_"))
    return s[:maxlen].rstrip("_-")


def suggest_name(story: dict) -> str:
    """Derive a filename from the story's first bolded entity."""
    m = re.search(r"\*\*(.+?)\*\*", story["text"])
    if m:
        first = re.sub(r"[^\w\s]", " ", m.group(1)).split()
        if first:
            cand = slugify(first[0])
            if len(cand) >= 3:
                return cand
    tag = re.match(r"^\s*\[([^\]]+)\]", story["text"])
    if tag:
        return slugify(tag.group(1))
    return slugify(story["section"].split(",")[0].split("&")[0]) or "img"


# --- markdown insertion -----------------------------------------------------

_write_lock = threading.Lock()


def insert_image(md_path: Path, story: dict, filename: str, alt: str) -> bool:
    """Insert (or replace) the image line directly ABOVE a story's paragraph.

    Placement matches published issues: in 2026/0705 every one of the 15 images
    sits above its story, never below.

    Re-locates the paragraph by its text rather than trusting a stored line
    number: earlier inserts shift every line below them, and the editor may
    also have the file open. Matching on content keeps this correct regardless.
    """
    with _write_lock:
        lines = md_path.read_text(encoding="utf-8").split("\n")
        needle = story["text"][:80]

        idx = next((i for i, l in enumerate(lines) if needle in l), None)
        if idx is None:
            return False

        img_line = f"![{alt}]({filename})"

        # Replace an existing image for this story if one is already there.
        for j in range(idx - 1, max(idx - 4, -1), -1):
            s = lines[j].strip()
            if not s:
                continue
            if re.match(r"^!\[[^\]]*\]\([^)]+\)", s):
                lines[j] = img_line
                md_path.write_text("\n".join(lines), encoding="utf-8")
                return True
            break  # hit a heading or prose — nothing to replace

        # Insert above the paragraph, keeping a blank line between them.
        lines.insert(idx, img_line)
        lines.insert(idx + 1, "")
        md_path.write_text("\n".join(lines), encoding="utf-8")
        return True


def download_and_normalize(url: str, dest_dir: Path, name: str):
    """Run the pick through fetch_image.sh so normalize rules stay in one place."""
    env = dict(os.environ)
    try:
        proc = subprocess.run(
            ["bash", str(FETCH_IMAGE), "--issue", dest_dir.name, url, name],
            capture_output=True, text=True, timeout=120, env=env,
            cwd=str(dest_dir), stdin=subprocess.DEVNULL,
        )
    except subprocess.TimeoutExpired:
        return None, "download timed out"

    out = proc.stdout + proc.stderr
    if proc.returncode != 0:
        msg = next((l.strip() for l in out.split("\n") if "✗" in l), "download failed")
        return None, re.sub(r"\x1b\[[0-9;]*m", "", msg).replace("✗", "").strip()

    m = re.search(r"^File:\s+(.+\.jpg)\s*$", re.sub(r"\x1b\[[0-9;]*m", "", out),
                  re.MULTILINE)
    if not m:
        return None, "could not determine output filename"
    return Path(m.group(1).strip()).name, None


# --- state ------------------------------------------------------------------

class PickerState:
    def __init__(self, issue_dir: Path, stories):
        self.issue_dir = issue_dir
        self.md_path = issue_dir / "index.md"
        self.stories = stories
        self.candidates = {}   # order -> [Candidate]
        self.queries = {}      # order -> str
        self.status = {}       # order -> "placed" | "skipped"
        self.lock = threading.Lock()

        for s in stories:
            self.queries[s["order"]] = build_query(s["text"], s["section"])
            if s["image"]:
                self.status[s["order"]] = "placed"

    def fetch(self, order: int, offset: int = 0, query: str = None,
              sources=None):
        q = query or self.queries[order]
        self.queries[order] = q
        cands = find_candidates(q, limit=CANDIDATES_PER_STORY, offset=offset,
                                sources=sources)
        with self.lock:
            self.candidates[order] = cands
        return cands


def prefetch_all(state: PickerState, workers: int = 3):
    """Warm the cache for every story before the browser opens.

    Searching on demand costs ~2s per story, which destroys the flip-through
    feel, so every story is warmed up front instead.

    Only 3 workers: Brave's free tier is ~1 req/s and is serialized behind a
    throttle in image_search, so more threads add contention without much gain.
    A few still help by overlapping request setup with the throttle wait.
    """
    todo = [s["order"] for s in state.stories
            if state.status.get(s["order"]) != "placed"]
    done = 0
    print(f"Searching {len(todo)} stories...", flush=True)
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(state.fetch, o): o for o in todo}
        for f in futures:
            pass
        for f in futures:
            try:
                f.result(timeout=90)
            except Exception:
                pass
            done += 1
            print(f"\r  {done}/{len(todo)}", end="", flush=True)
    print()


# --- http -------------------------------------------------------------------

class Handler(BaseHTTPRequestHandler):
    state: PickerState = None

    def log_message(self, *a):
        pass  # keep the terminal clean; errors still surface in responses

    def _json(self, obj, code=200):
        body = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _html(self, text: str):
        body = text.encode()
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        u = urlparse(self.path)
        q = parse_qs(u.query)
        st = self.state

        if u.path == "/":
            return self._html(PAGE)

        if u.path == "/api/stories":
            return self._json({
                "issue": st.issue_dir.name,
                "stories": [{
                    "order": s["order"],
                    "section": s["section"],
                    "text": s["text"],
                    "image": s["image"],
                    "status": st.status.get(s["order"]),
                    "query": st.queries[s["order"]],
                    "name": suggest_name(s),
                } for s in st.stories],
            })

        if u.path == "/api/candidates":
            order = int(q.get("order", [0])[0])
            offset = int(q.get("offset", [0])[0])
            query = q.get("q", [None])[0]
            srcs = q.get("sources", [None])[0]
            sources = srcs.split(",") if srcs else None

            with st.lock:
                cached = st.candidates.get(order)
            if cached is None or offset or query or sources:
                try:
                    cands = st.fetch(order, offset=offset, query=query,
                                     sources=sources)
                except Exception as e:
                    return self._json({"error": str(e)}, 500)
            else:
                cands = cached
            return self._json({
                "order": order,
                "query": st.queries[order],
                "candidates": [c.to_dict() for c in cands],
            })

        self.send_error(404)

    def do_POST(self):
        u = urlparse(self.path)
        st = self.state
        length = int(self.headers.get("Content-Length", 0))
        payload = json.loads(self.rfile.read(length) or b"{}")

        if u.path == "/api/pick":
            order = int(payload["order"])
            url = payload["url"]
            story = st.stories[order]
            name = slugify(payload.get("name") or suggest_name(story))
            # Alt text follows the published convention: a short subject label
            # matching the filename (e.g. "spiderman"), not the section name.
            alt = payload.get("alt") or name

            fname, err = download_and_normalize(url, st.issue_dir, name)
            if err:
                return self._json({"ok": False, "error": err}, 200)

            if not insert_image(st.md_path, story, fname, alt):
                return self._json(
                    {"ok": False, "error": "saved the file but could not locate "
                                           "the paragraph in index.md"}, 200)

            st.status[order] = "placed"
            story["image"] = fname
            return self._json({"ok": True, "file": fname})

        if u.path == "/api/skip":
            order = int(payload["order"])
            st.status[order] = "skipped"
            return self._json({"ok": True})

        self.send_error(404)


# --- page -------------------------------------------------------------------

PAGE = r"""<!doctype html>
<meta charset="utf-8">
<title>TSB Image Picker</title>
<style>
:root{
  --bg:#faf9f7; --card:#fff; --ink:#1a1a1a; --muted:#6b6b6b;
  --line:#e3e0db; --accent:#0b6; --warn:#c60;
}
@media (prefers-color-scheme:dark){
  :root{--bg:#16171a;--card:#1e2024;--ink:#e8e6e3;--muted:#9a9a9a;--line:#2f3237;}
}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);
  font:15px/1.55 -apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}
header{position:sticky;top:0;z-index:5;background:var(--card);
  border-bottom:1px solid var(--line);padding:10px 20px;
  display:flex;align-items:center;gap:16px}
h1{font-size:14px;margin:0;font-weight:600;letter-spacing:.02em}
.count{color:var(--muted);font-size:13px;margin-left:auto}
.dots{display:flex;gap:3px;flex-wrap:wrap;max-width:340px}
.dot{width:8px;height:8px;border-radius:50%;background:var(--line);cursor:pointer}
.dot.placed{background:var(--accent)} .dot.skipped{background:var(--warn)}
.dot.cur{outline:2px solid var(--ink);outline-offset:1px}
main{max-width:1080px;margin:0 auto;padding:22px 20px 60px}
.sect{font-size:11px;letter-spacing:.12em;text-transform:uppercase;
  color:var(--muted);margin-bottom:8px}
.story{background:var(--card);border:1px solid var(--line);border-radius:10px;
  padding:16px 18px;margin-bottom:18px;max-height:190px;overflow:auto}
.story b,.story strong{font-weight:650}
.grid{display:grid;grid-template-columns:repeat(3,1fr);gap:14px}
.cardw{background:var(--card);border:1px solid var(--line);border-radius:10px;
  overflow:hidden;cursor:pointer;transition:.12s;display:flex;flex-direction:column}
.cardw:hover{transform:translateY(-2px);border-color:var(--ink);
  box-shadow:0 6px 18px rgba(0,0,0,.12)}
.cardw.busy{opacity:.5;pointer-events:none}
.thumb{width:100%;aspect-ratio:4/3;object-fit:cover;background:var(--line);display:block}
.meta{padding:8px 10px;font-size:11px;color:var(--muted);line-height:1.4}
.meta .site{color:var(--ink);font-weight:550;word-break:break-all}
.tag{display:inline-block;padding:1px 6px;border-radius:4px;font-size:10px;
  background:var(--line);color:var(--ink);margin-right:4px}
.tag.brave{background:#fde8d7;color:#8a3b00}
.tag.wm{background:#fde3e3;color:#8a1c1c}
@media (prefers-color-scheme:dark){
  .tag.wm{background:#4a1717;color:#ffb4b4}
  .tag.brave{background:#4a2b12;color:#ffcfa3}
}
.controls{display:flex;gap:10px;align-items:center;margin:18px 0 8px;flex-wrap:wrap}
input[type=text]{flex:1;min-width:260px;padding:8px 11px;border:1px solid var(--line);
  border-radius:7px;background:var(--card);color:var(--ink);font-size:13px}
button{padding:8px 14px;border:1px solid var(--line);border-radius:7px;
  background:var(--card);color:var(--ink);cursor:pointer;font-size:13px}
button:hover{border-color:var(--ink)}
button.primary{background:var(--ink);color:var(--bg);border-color:var(--ink)}
.msg{padding:10px 14px;border-radius:8px;margin:12px 0;font-size:13px;display:none}
.msg.err{background:#fde8e8;color:#8a1c1c;display:block}
.msg.ok{background:#e3f7ec;color:#0a5c34;display:block}
@media (prefers-color-scheme:dark){
  .msg.err{background:#4a1717;color:#ffb4b4}.msg.ok{background:#12402a;color:#9fe9c2}
}
.empty{padding:36px;text-align:center;color:var(--muted);
  border:1px dashed var(--line);border-radius:10px}
.done{text-align:center;padding:50px 20px}
.done h2{font-size:20px;margin:0 0 10px}
kbd{background:var(--line);border-radius:4px;padding:1px 5px;font-size:11px}
</style>
<header>
  <h1>TSB Image Picker</h1>
  <div class="dots" id="dots"></div>
  <div class="count" id="count"></div>
</header>
<main id="app"><div class="empty">Loading…</div></main>
<script>
let S=[], i=0, issue="";

const esc = s => s.replace(/[&<>]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;'}[c]));
const md  = s => esc(s).replace(/\*\*(.+?)\*\*/g,'<b>$1</b>')
                       .replace(/`([^`]+)`/g,'<b>$1</b>');

async function boot(){
  const r = await (await fetch('/api/stories')).json();
  S = r.stories; issue = r.issue;
  document.title = 'TSB Picker · ' + issue;
  i = S.findIndex(s => !s.status);
  if (i < 0) i = 0;
  render();
}

function dots(){
  document.getElementById('dots').innerHTML = S.map((s,n)=>
    `<div class="dot ${s.status||''} ${n===i?'cur':''}" data-n="${n}" title="${n+1}. ${esc(s.section)}"></div>`
  ).join('');
  document.querySelectorAll('.dot').forEach(d=>
    d.onclick=()=>{i=+d.dataset.n;render();});
  const placed = S.filter(s=>s.status==='placed').length;
  const skipped = S.filter(s=>s.status==='skipped').length;
  document.getElementById('count').textContent =
    `${placed} placed · ${skipped} skipped · ${S.length} total`;
}

function render(){
  dots();
  const app = document.getElementById('app');
  if (i >= S.length){
    const sk = S.filter(s=>s.status==='skipped');
    app.innerHTML = `<div class="done"><h2>Done — ${S.filter(s=>s.status==='placed').length} images placed</h2>`
      + (sk.length ? `<p>Still without an image:</p><p>` +
          sk.map(s=>`<a href="#" onclick="i=${s.order};render();return false">${s.order+1}. ${esc(s.section)}</a>`).join(' · ')
          + `</p>` : `<p>Every story has an image.</p>`)
      + `<p style="color:var(--muted);font-size:13px">index.md has been updated. Review with <kbd>git diff</kbd>.</p></div>`;
    return;
  }
  const s = S[i];
  app.innerHTML = `
    <div class="sect">${esc(s.section)} · story ${i+1} of ${S.length}${s.status?' · '+s.status:''}</div>
    <div class="story">${md(s.text)}</div>
    <div class="msg" id="msg"></div>
    <div class="controls">
      <input type="text" id="q" value="${esc(s.query)}" placeholder="search query">
      <button onclick="search()">Search</button>
      <button onclick="more()">↻ More</button>
      <button onclick="skip()">Skip</button>
      <button onclick="if(i>0){i--;render()}">← Back</button>
      <button class="primary" onclick="if(i<S.length){i++;render()}">Next →</button>
    </div>
    <div class="grid" id="grid"><div class="empty">Searching…</div></div>`;
  document.getElementById('q').addEventListener('keydown', e=>{
    if(e.key==='Enter') search();
  });
  load(0);
}

let offset = 0;
async function load(off, q){
  offset = off;
  const grid = document.getElementById('grid');
  grid.innerHTML = '<div class="empty">Searching…</div>';
  let url = `/api/candidates?order=${S[i].order}&offset=${off}`;
  if (q) url += '&q=' + encodeURIComponent(q);
  try{
    const r = await (await fetch(url)).json();
    if (r.query) document.getElementById('q').value = r.query;
    show(r.candidates || []);
  }catch(e){ grid.innerHTML = `<div class="empty">Search failed: ${esc(''+e)}</div>`; }
}

function show(cs){
  const grid = document.getElementById('grid');
  if (!cs.length){
    grid.innerHTML = `<div class="empty">No candidates. Try editing the query above,
      or <a href="#" onclick="more();return false">search for more</a>.</div>`;
    return;
  }
  grid.innerHTML = cs.map((c,n)=>`
    <div class="cardw" data-n="${n}">
      <img class="thumb" src="${esc(c.thumb)}" loading="lazy"
           onerror="this.src='${esc(c.url)}'">
      <div class="meta">
        <span class="tag ${c.source}">${c.source}</span>
        ${c.watermark?'<span class="tag wm" title="stock library — likely watermarked">watermark?</span>':''}
        ${c.width}×${c.height}<br>
        <span class="site">${esc(c.site||'')}</span>
        ${c.license?'<br>'+esc(c.license):''}
      </div>
    </div>`).join('');
  document.querySelectorAll('.cardw').forEach(el=>{
    el.onclick = ()=> pick(cs[+el.dataset.n], el);
  });
}

async function pick(c, el){
  el.classList.add('busy');
  msg('Downloading and inserting…','ok');
  const r = await (await fetch('/api/pick',{
    method:'POST', headers:{'Content-Type':'application/json'},
    body: JSON.stringify({order:S[i].order, url:c.url, name:S[i].name,
                          alt:S[i].name})
  })).json();
  if(!r.ok){ el.classList.remove('busy'); msg(r.error||'failed','err'); return; }
  S[i].status='placed'; S[i].image=r.file;
  i++; render();
}

async function skip(){
  await fetch('/api/skip',{method:'POST',headers:{'Content-Type':'application/json'},
    body:JSON.stringify({order:S[i].order})});
  S[i].status='skipped'; i++; render();
}

function more(){ load(offset + 3); }
function search(){ load(0, document.getElementById('q').value); }
function msg(t,k){ const m=document.getElementById('msg');
  if(!m) return; m.textContent=t; m.className='msg '+k; }

document.addEventListener('keydown', e=>{
  if(e.target.tagName==='INPUT') return;
  if(e.key==='ArrowRight'&&i<S.length){i++;render();}
  if(e.key==='ArrowLeft'&&i>0){i--;render();}
  if(e.key==='r') more();
  if(e.key==='s') skip();
  if(['1','2','3'].includes(e.key)){
    const el=document.querySelectorAll('.cardw')[+e.key-1]; if(el) el.click();
  }
});
boot();
</script>
"""


def main():
    ap = argparse.ArgumentParser(description="Pick images for a TSB issue.")
    ap.add_argument("--issue", required=True, help="YYYYMMDD or MMDD")
    ap.add_argument("--port", type=int, default=8420)
    ap.add_argument("--no-prefetch", action="store_true",
                    help="search lazily instead of warming all stories first")
    ap.add_argument("--no-open", action="store_true",
                    help="do not open a browser automatically")
    args = ap.parse_args()

    issue_dir = resolve_issue_dir(args.issue)
    md_path = issue_dir / "index.md"
    if not md_path.exists():
        raise SystemExit(f"No index.md in {issue_dir}")

    stories = parse_stories(md_path)
    if not stories:
        raise SystemExit("No image-eligible stories found in index.md")

    if not os.environ.get("BRAVE_API_KEY"):
        raise SystemExit(
            "BRAVE_API_KEY is not set, and Brave is the only image source.\n"
            "  It lives in ~/.secrets; load it with:  source ~/.secrets\n"
            "  (New shells pick it up automatically.)")

    state = PickerState(issue_dir, stories)
    already = sum(1 for s in stories if s["image"])
    print(f"Issue {issue_dir.name}: {len(stories)} stories"
          + (f" ({already} already have images)" if already else ""))

    if not args.no_prefetch:
        prefetch_all(state)

    Handler.state = state
    srv = ThreadingHTTPServer(("127.0.0.1", args.port), Handler)
    url = f"http://localhost:{args.port}"
    total = sum(len(v) for v in state.candidates.values())
    print(f"\n  {total} candidates ready → {url}")
    print("  Click an image to place it. Ctrl-C when done.\n")
    if not args.no_open:
        threading.Timer(0.6, lambda: webbrowser.open(url)).start()
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        placed = sum(1 for v in state.status.values() if v == "placed")
        print(f"\nStopped. {placed} images placed in {md_path}")


if __name__ == "__main__":
    main()
