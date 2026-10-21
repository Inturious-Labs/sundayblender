#!/usr/bin/env python3
"""Write xhs/NN-key/post.txt (title, body, hashtags) for each post in xhs-drafts.md.

Usage: xhs_posttxt.py ISSUE_DIR KEY1 ... KEY7   (folder names, in posting order)
"""
import re, sys
from pathlib import Path
issue_dir = Path(sys.argv[1]); keys = sys.argv[2:]
s = (issue_dir / "xhs-drafts.md").read_text().split("# Card 2 text")[0]
for n, key in enumerate(keys, 1):
    sec = re.search(rf"^## {n}/7 .*?\n(.*?)\n---\n", s, re.M | re.S).group(1)
    title = re.search(r"\*\*Title:\*\* (.+)", sec).group(1)
    body = re.search(r"\*\*Body:\*\*\n(.*?)\n\n\*\*Vocab", sec, re.S).group(1).strip()
    tags = re.search(r"\*\*Tags:\*\* (.+)", sec).group(1).replace("#", "").split()
    d = issue_dir / "xhs" / f"{n:02d}-{key}"; d.mkdir(parents=True, exist_ok=True)
    tagline = " ".join("#" + t for t in tags)
    (d / "post.txt").write_text(f"\u3010\u6807\u9898\u3011\n{title}\n\n\u3010\u6b63\u6587\u3011\n{body}\n\n{tagline}\n")
    print(d / "post.txt")
