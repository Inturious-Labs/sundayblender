#!/usr/bin/env python3
"""Render Red Note cards for one post from xhs-drafts.md + index.md.

Usage: xhs_cards.py ISSUE_DIR N IMAGE_KEY OUT_DIR
  e.g. xhs_cards.py . 1 tesla xhs/01-tesla   (from the issue folder)
"""
import html, re, subprocess, sys, tempfile
from pathlib import Path

CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
LOGO = (Path(__file__).resolve().parents[1] / "static/img/logo.png").as_uri()
W, H = 1080, 1440
MAX_WORDS = 160  # one story card holds about this many words at 38px

issue_dir = Path(sys.argv[1]).resolve(); n = int(sys.argv[2]); key = sys.argv[3]; out = Path(sys.argv[4]).resolve()
drafts = (issue_dir / "xhs-drafts.md").read_text()
index = (issue_dir / "index.md").read_text()
issue = re.search(r"^issue:\s*(\d+)", index, re.M).group(1)

body = re.search(rf"^## {n}/7 · .*?\n(.*?)\n---\n", drafts, re.M | re.S).group(1)
hook = re.search(r"\*\*Cover hook:\*\* (.+)", body).group(1).strip()
headline = re.search(r"\*\*Cover English:\*\* (.+)", body).group(1).strip()
vocab = re.findall(r"^- (.+?) (/.+?/) (.+)$", body, re.M)
qs = re.findall(r"^\d\. (.+)\n\s+提示[:：](.+)$", body, re.M)

# Story paragraph with bold kept; section from the nearest heading above it.
lines = index.splitlines()
i = next(i for i, l in enumerate(lines) if re.search(rf"\(\./{re.escape(key)}\.", l))
section = next(l[3:] for l in reversed(lines[:i]) if l.startswith("## "))
story = next(l for l in lines[i + 1:] if l.strip()).replace("`", "")
photo = (issue_dir / next(p.name for p in issue_dir.iterdir() if p.stem == key)).as_uri()

# Split long stories at the sentence boundary nearest the middle.
sentences = re.split(r"(?<=[.!?”\"])\s+(?=[A-Z“\"*])", story)
parts = [story]
if len(story.split()) > MAX_WORDS:
    half, count = len(story.split()) / 2, 0
    for k, sent in enumerate(sentences):
        count += len(sent.split())
        if count >= half:
            parts = [" ".join(sentences[:k + 1]), " ".join(sentences[k + 1:])]
            break

todo = [w for w, _, _ in vocab]
def markup(text):
    text = html.escape(text.replace("“", '"').replace("”", '"'))
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
    for w in list(todo):
        base = w[:-1] if w.endswith("e") and len(w) > 4 else w
        pat = rf"\b({re.escape(base)}\w{{0,4}})\b"
        if re.search(pat, text, re.I):
            text = re.sub(pat, r"<u>\1</u>", text, count=1, flags=re.I)
            todo.remove(w)
    return text

CSS = f"""
*{{margin:0;padding:0;box-sizing:border-box}}
body{{width:{W}px;height:{H}px;background:#f6ecdc;color:#3d2615;
  font-family:"PingFang SC","Hiragino Sans GB",sans-serif;position:relative;overflow:hidden}}
.serif{{font-family:Georgia,"Songti SC",serif}}
.foot{{position:absolute;left:0;right:0;bottom:0;height:110px;background:#5c3a1f;color:#f0dcbc;
  display:flex;align-items:center;padding:0 56px;gap:22px;font-size:30px}}
.foot img{{width:64px;height:64px;border-radius:12px}}
.foot .r{{margin-left:auto;opacity:.8}}
.tag{{display:inline-block;background:#5c3a1f;color:#f0dcbc;font-size:30px;padding:10px 26px;border-radius:40px}}
.pad{{padding:72px 64px 0}}
h2{{font-size:52px;margin:28px 0 40px}}
"""
def foot(label): return f'<div class="foot"><img src="{LOGO}"><span>The Sunday Blender · Issue {issue}</span><span class="r">{label}</span></div>'

cards = [("cover", f"""<style>{CSS}
.ph{{height:820px;background:url('{photo}') center/cover}}
.hk{{font-size:{92 if len(hook) <= 10 else 76}px;font-weight:700;line-height:1.2;margin:40px 0 24px}}
.en{{font-size:40px;font-style:italic;opacity:.75}}</style>
<div class="ph"></div><div class="pad" style="padding-top:44px">
<span class="tag">TSB 英文周报 · 第 {issue} 期 · {n}/7</span>
<div class="hk">{hook}</div><div class="en serif">{html.escape(headline)}</div></div>{foot("英文新闻")}""")]

for k, part in enumerate(parts, 1):
    label = f"Read in English · {html.escape(section)}" + (f" · {k}/{len(parts)}" if len(parts) > 1 else "")
    nxt = "划线词见下一张 →" if k == len(parts) else "接下一张 →"
    cards.append(("story", f"""<style>{CSS}
.st{{font-size:38px;line-height:1.6}} .st b{{background:#f0d29a;padding:0 4px;border-radius:4px}}
.st u{{text-decoration-color:#c0702a;text-decoration-thickness:4px;text-underline-offset:6px}}</style>
<div class="pad"><span class="tag">\U0001F4D6 {label}</span>
<div class="st serif" style="margin-top:44px">{markup(part)}</div></div>{foot(nxt)}"""))

rows = "".join(f'<div class="v"><div><span class="w serif">{html.escape(w)}</span> <span class="ipa">{p}</span></div><div class="zh">{z}</div></div>' for w, p, z in vocab)
cards.append(("vocab", f"""<style>{CSS}
.v{{display:flex;justify-content:space-between;align-items:center;gap:24px;padding:34px 0;border-bottom:3px dashed #d9bf98}}
.w{{font-size:64px;font-weight:700}} .ipa{{font-size:36px;opacity:.65;margin-left:16px}} .zh{{font-size:44px;text-align:right}}</style>
<div class="pad"><span class="tag">\U0001F4DD 核心词汇 · Key Words</span><h2>文中划线的 5 个词</h2>{rows}</div>{foot("跟读三遍 \U0001F501")}"""))

qrows = "".join(f'<div class="q"><div class="n">Q{k}</div><div class="en serif">{html.escape(q)}</div><div class="hint">\U0001F4A1 {h}</div></div>' for k, (q, h) in enumerate(qs, 1))
cards.append(("ask", f"""<style>{CSS}
.q{{background:#fffaf2;border-radius:28px;padding:44px;margin-bottom:40px;box-shadow:0 6px 0 #e3cba6}}
.n{{font-size:34px;font-weight:700;color:#c0702a}} .en{{font-size:50px;line-height:1.35;margin:14px 0 22px}}
.hint{{font-size:36px;opacity:.75}} .save{{text-align:center;font-size:44px;font-weight:700;margin-top:30px}}</style>
<div class="pad"><span class="tag">\U0001F4AC 亲子讨论 · Talk About It</span><h2>读完问问孩子</h2>{qrows}
<div class="save">\U0001F4CC 收藏起来，周末和孩子一起读</div></div>{foot("明天见 \U0001F44B")}"""))

out.mkdir(parents=True, exist_ok=True)
for old in out.glob("*.png"):
    old.unlink()
with tempfile.TemporaryDirectory() as tmp:
    for num, (name, doc) in enumerate(cards, 1):
        f = Path(tmp) / f"{num}.html"
        f.write_text(f'<!doctype html><meta charset="utf-8"><body>{doc}</body>')
        png = out / f"{num}-{name}.png"
        subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--force-device-scale-factor=1",
                        f"--window-size={W},{H}", f"--screenshot={png}", "--allow-file-access-from-files",
                        f.as_uri()], check=True, capture_output=True)
        print(png)
if todo:
    print("WARNING: vocab not found in story, no underline:", ", ".join(todo))
