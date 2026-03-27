#!/usr/bin/env python3
"""ppt_aux_instructor_build_guide.md → 단일 HTML (표·코드·목차)."""

from __future__ import annotations

import argparse
from pathlib import Path

import markdown
from markdown.extensions.toc import TocExtension

_PLANS = Path(__file__).resolve().parents[1]  # docs/plans
DEFAULT_MD = _PLANS / "ppt_aux_instructor_build_guide.md"
DEFAULT_OUT = _PLANS / "ppt_aux_instructor_build_guide.html"

_GOOGLE_FONT_HREF = (
    "https://fonts.googleapis.com/css2?"
    "family=Noto+Sans+KR:wght@400;500;600;700&"
    "family=Source+Serif+4:ital,opsz,wght@0,8..60,400;0,8..60,600;1,8..60,400&"
    "display=swap"
)

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>PPT 보조강사 가이드 — HTML 뷰</title>
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
  <link href="__FONT_HREF__" rel="stylesheet" />
  <style>
    :root {
      --bg: #f4f1ea;
      --paper: #fdfcfa;
      --ink: #1e2422;
      --muted: #5c6562;
      --accent: #1a5f5a;
      --accent-soft: #e3f0ef;
      --border: #d4cfc4;
      --code-bg: #ebe6dc;
      --shadow: 0 1px 3px rgba(30, 36, 34, 0.08);
    }
    * { box-sizing: border-box; }
    html { scroll-behavior: smooth; }
    body {
      margin: 0;
      font-family: "Noto Sans KR", system-ui, sans-serif;
      font-size: 15px;
      line-height: 1.65;
      color: var(--ink);
      background: var(--bg);
    }
    .shell {
      max-width: 1200px;
      margin: 0 auto;
      padding: 1.25rem 1rem 3rem;
      display: grid;
      grid-template-columns: minmax(0, 1fr) 260px;
      gap: 2rem;
      align-items: start;
    }
    @media (max-width: 960px) {
      .shell {
        grid-template-columns: 1fr;
        padding: 1rem;
      }
      .toc-wrap {
        position: static !important;
        order: -1;
      }
    }
    .banner {
      grid-column: 1 / -1;
      background: linear-gradient(135deg, var(--accent-soft) 0%, var(--paper) 55%);
      border: 1px solid var(--border);
      border-radius: 10px;
      padding: 0.85rem 1.1rem;
      font-size: 0.88rem;
      color: var(--muted);
      box-shadow: var(--shadow);
    }
    .banner strong { color: var(--accent); }
    article.doc {
      background: var(--paper);
      border: 1px solid var(--border);
      border-radius: 12px;
      padding: 1.75rem 2rem 2.5rem;
      box-shadow: var(--shadow);
      min-width: 0;
    }
    .doc h1 {
      font-family: "Source Serif 4", "Noto Sans KR", serif;
      font-size: 1.75rem;
      font-weight: 600;
      margin: 0 0 1rem;
      letter-spacing: -0.02em;
      color: var(--ink);
      border-bottom: 2px solid var(--accent);
      padding-bottom: 0.5rem;
    }
    .doc h2 {
      font-size: 1.2rem;
      font-weight: 700;
      margin: 2rem 0 0.75rem;
      color: var(--accent);
    }
    .doc h3 {
      font-size: 1.05rem;
      font-weight: 600;
      margin: 1.35rem 0 0.5rem;
      color: var(--ink);
    }
    .doc h4 {
      font-size: 0.98rem;
      font-weight: 600;
      margin: 1rem 0 0.4rem;
    }
    .doc p { margin: 0.65rem 0; }
    .doc ul, .doc ol { margin: 0.5rem 0 0.75rem; padding-left: 1.35rem; }
    .doc li { margin: 0.25rem 0; }
    .doc blockquote {
      margin: 1rem 0;
      padding: 0.65rem 1rem;
      border-left: 4px solid var(--accent);
      background: var(--accent-soft);
      color: var(--muted);
      font-size: 0.95rem;
    }
    .doc blockquote p { margin: 0.4rem 0; }
    .doc hr {
      border: none;
      border-top: 1px solid var(--border);
      margin: 1.75rem 0;
    }
    .doc a { color: var(--accent); text-decoration: underline; text-underline-offset: 2px; }
    .doc a:hover { opacity: 0.85; }
    .doc code {
      font-family: ui-monospace, "Cascadia Code", monospace;
      font-size: 0.86em;
      background: var(--code-bg);
      padding: 0.12em 0.35em;
      border-radius: 4px;
    }
    .doc pre {
      margin: 1rem 0;
      padding: 1rem 1.1rem;
      background: #2b2d2c;
      color: #e8e6e1;
      border-radius: 8px;
      overflow-x: auto;
      font-size: 0.84rem;
      line-height: 1.5;
    }
    .doc pre code {
      background: none;
      padding: 0;
      color: inherit;
      font-size: inherit;
    }
    .doc table {
      width: 100%;
      border-collapse: collapse;
      margin: 1rem 0;
      font-size: 0.88rem;
      box-shadow: var(--shadow);
      border-radius: 8px;
      overflow: hidden;
    }
    .doc th, .doc td {
      border: 1px solid var(--border);
      padding: 0.5rem 0.65rem;
      text-align: left;
      vertical-align: top;
    }
    .doc th {
      background: var(--accent-soft);
      font-weight: 600;
      color: var(--ink);
    }
    .doc tr:nth-child(even) td { background: #f9f7f3; }
    .toc-wrap {
      position: sticky;
      top: 1rem;
      font-size: 0.8rem;
      line-height: 1.45;
    }
    .toc-inner {
      background: var(--paper);
      border: 1px solid var(--border);
      border-radius: 10px;
      padding: 1rem 1rem 1.1rem;
      box-shadow: var(--shadow);
      max-height: calc(100vh - 2rem);
      overflow-y: auto;
    }
    .toc-inner .label {
      font-weight: 700;
      color: var(--accent);
      margin-bottom: 0.6rem;
      font-size: 0.75rem;
      text-transform: uppercase;
      letter-spacing: 0.06em;
    }
    .toc ul {
      list-style: none;
      margin: 0;
      padding: 0;
    }
    .toc ul ul { padding-left: 0.85rem; margin-top: 0.25rem; }
    .toc li { margin: 0.2rem 0; }
    .toc a {
      color: var(--muted);
      text-decoration: none;
      display: block;
      border-radius: 4px;
      padding: 0.15rem 0.25rem;
    }
    .toc a:hover { background: var(--accent-soft); color: var(--accent); }
    footer.gen {
      grid-column: 1 / -1;
      text-align: center;
      font-size: 0.78rem;
      color: var(--muted);
      margin-top: 0.5rem;
    }
  </style>
</head>
<body>
  <div class="shell">
    <div class="banner">
      <strong>원본</strong> <code>docs/plans/ppt_aux_instructor_build_guide.md</code> —
      갱신 시
      <code>python3 docs/plans/scripts/render_ppt_aux_instructor_build_guide_html.py</code>
      로 이 HTML을 다시 생성하세요.
    </div>
    <article class="doc" id="top">
__BODY__
    </article>
    <aside class="toc-wrap">
      <nav class="toc-inner toc" aria-label="목차">
        <div class="label">목차</div>
__TOC__
      </nav>
    </aside>
    <footer class="gen">IDR lis_cursor · PPT 보조강사 가이드 HTML 뷰</footer>
  </div>
</body>
</html>
"""


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=DEFAULT_MD)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()
    text = args.input.read_text(encoding="utf-8")
    md = markdown.Markdown(
        extensions=[
            "markdown.extensions.tables",
            "markdown.extensions.fenced_code",
            TocExtension(toc_depth="2-4", permalink=False),
        ]
    )
    body = md.convert(text)
    toc = md.toc or "<p><em>목차 없음</em></p>"
    out = HTML_TEMPLATE.replace("__BODY__", body).replace("__TOC__", toc).replace("__FONT_HREF__", _GOOGLE_FONT_HREF)
    args.output.write_text(out, encoding="utf-8")
    print(f"Wrote {args.output} ({len(out):,} bytes)")


if __name__ == "__main__":
    main()
