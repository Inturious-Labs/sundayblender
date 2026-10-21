---
name: tsb-rednote
description: Turn a published issue of The Sunday Blender (TSB) into a week of Red Note (小红书 / Xiaohongshu / RedNote) drafts — seven bilingual posts aimed at Chinese parents, written in the exact file format the TSB card scripts parse. Use this skill whenever the user mentions Red Note, RedNote, 小红书， Xiaohongshu, XHS, "xhs drafts", or asks to turn TSB stories into posts for Chinese parents — even if they only paste an issue and a list of story names.
---

# The Sunday Blender — Red Note drafts

Turn seven stories from one TSB issue into seven Red Note drafts, one post a day for
a week. The output is a single Markdown file, `xhs-drafts.md`, that the editor drops
into the issue folder. Two scripts then read it: one renders the image cards, the
other writes the text the editor pastes into Red Note. **The scripts parse the file
line by line, so the format below is a contract, not a style suggestion.**

## Who reads it

Chinese parents, not kids. A parent finds a post through Red Note's search and
recommendations, saves it (收藏), and reads it later with a child aged 8-15, or
forwards it. The English story is the product; the Chinese around it helps the
parent use it. Write for a busy parent with average English.

## What one post is

Image cards (rendered by the script, not by you):

1. Cover: the story photo, the **Cover hook** in large Chinese, the **Cover English** line
2. The English story, exactly as published (two cards if it runs over 160 words)
3. Five vocabulary words from the story, with phonetics and Chinese
4. Two questions for the parent to ask, with Chinese hints

Text the editor pastes: the **Title**, the **Body**, and the **Tags** line.

## Input

The user supplies:

- The issue's `index.md` (or the issue number plus the seven stories pasted in)
- The seven stories, in posting order, named by image filename or short label
- Optionally the first posting date. Default: the Monday after the issue date.

Use the stories as published. They were fact-checked when the issue was written; do
not re-research them, and do not add facts that are not in the story. The one
exception is an approximate RMB conversion for a money figure ("约 10 万元人民币"),
which must say 约 and be listed in the notes.

If the user names fewer or more than seven stories, ask. Do not pick stories for them.

## Story check (before drafting)

The user picks the stories, but flag any that could hurt a new account in China, and
suggest a swap from the same issue. Do not swap without asking. Flag:

- Anything about Chinese policy, Taiwan, Hong Kong, Xinjiang, Tibet, protests,
  elections, or territorial disputes
- War, wartime commemoration, or Japanese shrines and imperial history
- Stories that cast any country as a villain
- Two stories from the same country or category in one week

Good fits: animals, space, robots, sports stars, Chinese achievements abroad or at
home, odd science, funny contests, math puzzles.

## Format contract

Output the whole file in one fenced code block, nothing else inside it. Exact shape:

```
# Red Note drafts: TSB Issue {N} ({Mon DD}–{DD}, {YYYY})

Each post: Card 1 cover · Card 2 English story (2a/2b if long) · Card 3 vocab · Card 4 questions.
Body text below is ready to paste. Post at 20:00 Beijing time.

---

## 1/7 · {Day} {Mon} {DD} · {Short English label}

**Cover hook:** ...
**Cover English:** ...
**Title:** ...

**Body:**
...

**Vocab:**
- word /ipa/ 中文
(five lines)

**Questions:**
1. English question?
   提示：中文提示
2. English question?
   提示：中文提示

**Tags:** #... #...

---
```

Rules the scripts depend on:

- Section heading is exactly `## n/7 · Ddd Mmm D · Label` with `·` (middle dot) and
  spaces. Every section, including the seventh, ends with a line `---`.
- Labels are exactly `**Cover hook:**`, `**Cover English:**`, `**Title:**`,
  `**Body:**`, `**Vocab:**`, `**Questions:**`, `**Tags:**`, with one space after
  the colon on the one-line labels.
- `**Body:**` is on its own line; the body follows; then one blank line; then
  `**Vocab:**`. The body may contain blank lines.
- Each vocab line: `- word /ipa/ 中文`. One space between the three parts.
- Each question: `1. ` + English, then a new line indented three spaces with `提示：`
  + Chinese.
- Dates: work out the weekday with code if you can run it. Never guess a weekday.

## Field rules

**Cover hook.** A short Chinese punchline, 12 characters or fewer, that reads in one
glance over a photo. It must not repeat the title; the two appear next to each other
in the feed. The hook is the visual joke or surprise; the title carries the search
words. Examples: 跑车，起飞了！ / 再见了，梅西 / 从第 54 名到冠军.

**Cover English.** Six words or fewer, sentence case, a plain English label for the
story: Tesla's flying sports car / A race to fall asleep.

**Title.** Chinese, 20 characters or fewer counting emoji and spaces. Include the
words a parent would search: the famous name, the thing, the place. A question or a
surprising number works well. At most one emoji, at the end.

**Body.** This template, every time:

```
The Sunday Blender 英文周报 第 {N} 期 · {n}/7

{One or two sentences: what happened, in plain Chinese, with one emoji at the end.}

{A short lead-in line ending in ：， then 2-3 emoji bullets with the key facts.}

{Optional one-line closer: the most surprising fact in the story.}

👉 第 2 张英文原文 · 第 3 张核心词汇 · 第 4 张亲子讨论题
📌 收藏起来，周末和孩子一起读
```

- Always spell out "The Sunday Blender" in the first line, never "TSB". Parents who
  want more search for that name; there are no links on Red Note.
- The 👉 line depends on story length. Count the published story's words (split on
  spaces). Over 160 words means the story takes two cards, so the line becomes
  `👉 第 2-3 张英文原文 · 第 4 张核心词汇 · 第 5 张亲子讨论题`.
- Bullet emoji: pick ones that match the fact (🔥 🌱 ⚽ 🧠). ✅ when there's nothing
  better. No plain "-" or "•" bullets.
- About 150-250 Chinese characters. Red Note's limit is 1,000 including tags.
- No links, URLs, email addresses, QR references, "订阅", or names of other apps.
  Red Note limits posts that send people elsewhere.

**Vocab.** Five words that appear in the story, in the form the story uses or as the
base form of one (the script underlines the first match, allowing -s/-ed/-ing
endings). Choose words a 10-year-old learner wouldn't know but would meet again:
not proper nouns, not numbers, not words explained away in the story itself. A
two-word term is fine if it appears as is ("brain wave"). American IPA with stress
marks: /ˈnɑːzəl/. The Chinese is the meaning in this story, short (2-6 characters).

**Questions.** Two, in simple English a child can answer out loud:

1. A comprehension question whose answer is in the story. The hint says where to look
   (提示：答案在倒数第三句 / 提示：找找 “panic” 这个词).
2. A personal or opinion question with no right answer. The hint gives the parent a
   way in (提示：用 “Thank you for…” 开头试试 / 提示：说出你的理由，没有标准答案).

No moral lesson and no "what should we learn" question.

**Tags.** Six. Always these four first: `#英文阅读 #英语启蒙 #英文新闻 #少儿英语`. Then two
about the story: one category (#科技新闻 #足球 #趣味数学 #历史故事 #环境保护) and one
specific name (#特斯拉 #梅西 #郑钦文). Never `#双语新闻`: the news is in English; the
Chinese only supports it.

## Chinese typography

These apply to every Chinese field: hook, title, body, vocab meanings, hints.

- **Full-width punctuation** in Chinese text: ，。？！：；（）“”. Half-width only inside an
  English phrase: 他最后说：“I leave grateful, proud and at peace.”
- **A space between Chinese and English or digits**, both sides: 在 SpaceX 测试场 /
  第 67 期 / 8.5 万人 / 10 月 6 日. No space next to full-width punctuation.
- Standard Chinese names for people and places (梅西， 布宜诺斯艾利斯， 安德烈耶娃).
  Keep brand and product names in English (Roadster, Deezer).

## Voice

Same promises as the newsletter: no pressure, no politics, no lecturing, no
patronizing. In practice:

- No filler openers (今天给大家分享， 宝妈们注意了， 家人们). Start with the fact.
- No hype words the story doesn't support (震惊， 炸裂， 必看).
- Parent-to-parent warmth is fine (周末和孩子一起读); selling is not.

## After the code block

Short notes, outside the file:

- Stories flagged in the story check, and why
- Any RMB conversion or other figure you derived
- Which posts take two story cards
- Anything in the story you could not express cleanly in Chinese

## Self-check before showing the file

1. Seven sections, numbered 1/7 to 7/7, each ending with `---`.
2. Every weekday was computed, not guessed, and the dates run on consecutive days.
3. Every label spelled exactly as in the contract; `提示：` on every hint.
4. Cover hook ≤ 12 characters and different from the title; title ≤ 20 characters.
5. Body starts with "The Sunday Blender 英文周报"; the 👉 line matches the word count.
6. All five vocab words appear in the story; IPA in slashes.
7. Full-width punctuation throughout the Chinese, half-width only inside English.
8. A space between every Chinese character and an adjacent letter or digit.
9. Tags start with the four fixed ones; no #双语新闻.
10. No fact in the Chinese that isn't in the English story.

## Worked example

One section from issue 67, as it was posted:

```
## 1/7 · Mon Oct 19 · Tesla

**Cover hook:** 跑车，起飞了！
**Cover English:** Tesla's flying sports car
**Title:** 特斯拉的跑车会飞了？！🚗

**Body:**
The Sunday Blender 英文周报 第 67 期 · 1/7

特斯拉在美国德州的 SpaceX 测试场，让一辆无人驾驶的新款 Roadster 开上弯道、倒着跑、腾空翻滚，再稳稳落地🚗💨

秘密有两个：
✅ 车底风扇把空气“吸走”，车就牢牢贴在路面上
✅ 高压空气从 10 个喷嘴喷出，把车推上天

👉 第 2 张英文原文 · 第 3 张核心词汇 · 第 4 张亲子讨论题
📌 收藏起来，周末和孩子一起读

**Vocab:**
- ramp /ræmp/ 坡道
- nozzle /ˈnɑːzəl/ 喷嘴
- thruster /ˈθrʌstər/ 推进器
- grip /ɡrɪp/ 抓地力
- pressure /ˈpreʃər/ 压力

**Questions:**
1. How does the car stay on the ramp when it is upside down?
   提示：找找文中风扇的作用
2. Would you ride in a flying car? Why or why not?
   提示：说说你喜欢的地方和担心的地方

**Tags:** #英文阅读 #英语启蒙 #英文新闻 #少儿英语 #科技新闻 #特斯拉

---
```
