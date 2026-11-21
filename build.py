#!/usr/bin/env python3
"""Build the CEO Inflection issues site.

Each issue lives in issues/<YYYY-MM>/issue.json. Running this script renders, for every issue:
  issues/<id>/index.html  page-turning edition (works on its own or inside an iframe)
  issues/<id>/print.html  print layout used to make the PDF
  issues/<id>/CEO-Inflection-<id>.pdf  (when --pdf is passed and Chrome/Playwright is available)
and regenerates the archive (index.html), latest/index.html (always points at the newest issue)
and issues.json.

issue.json shape:
{
  "id": "2026-12", "label": "December 2026", "vol": "Vol. 1 · No. 1",
  "intro": ["paragraph", "paragraph"],
  "picks": [{"cat": "", "source": "", "author": "", "title": "", "url": "", "image": "", "summary": ""}]
}
"""
import html, json, sys, pathlib

ROOT = pathlib.Path(__file__).resolve().parent
SUBSCRIBE = "https://ceoinflection.com"
E = lambda s: html.escape(str(s or ""), quote=True)

FONTS = '<link rel="preconnect" href="https://fonts.googleapis.com"><link href="https://fonts.googleapis.com/css2?family=Abril+Fatface&family=Cinzel:wght@600;700&family=Source+Serif+4:ital,opsz,wght@0,8..60,400;0,8..60,600;0,8..60,700;1,8..60,400&family=IBM+Plex+Sans+Condensed:wght@500;600&display=swap" rel="stylesheet">'

BASE_CSS = """
:root{--paper:#1f2023;--page:#f7f4ee;--ink:#17181b;--ink2:#4a4741;--rule:#d3cbbd;--accent:#8a6540;--bronze:#c19a6b;--desk:#1f2023;--card:#2a2b2f;--line:#3b3c41;--light:#efe9df;--muted:#b3ab9e;
--display:"Abril Fatface","Bodoni 72",Didot,Georgia,serif;--body:"Source Serif 4",Georgia,"Times New Roman",serif;
--label:"IBM Plex Sans Condensed","Arial Narrow",Arial,sans-serif;color-scheme:light}
*{box-sizing:border-box}html,body{margin:0}
body{font:16px/1.55 var(--body);color:var(--ink);-webkit-font-smoothing:antialiased}
a:focus-visible,button:focus-visible{outline:2px solid var(--accent);outline-offset:2px}
.page{background:var(--page);color:var(--ink);overflow:hidden;container-type:size}
.pg{height:100%;padding:22px 24px 18px;display:flex;flex-direction:column;gap:10px}
.folio{display:flex;justify-content:space-between;font:600 10px var(--label);letter-spacing:.12em;text-transform:uppercase;color:var(--ink2);border-bottom:1px solid var(--ink);padding-bottom:6px}
.folio.bot{border-bottom:0;border-top:1px solid var(--rule);padding:6px 0 0;margin-top:auto}
.mast{text-align:center;border-bottom:4px double var(--ink);padding-bottom:8px}
.mast .t{font:700 34px/1.05 "Cinzel",var(--display);letter-spacing:.04em;text-transform:uppercase}
.mast .s{font:600 9px var(--label);letter-spacing:.14em;text-transform:uppercase;color:var(--ink2);margin-top:6px;display:flex;flex-wrap:wrap;justify-content:center;gap:2px 0}
.mast .s span:nth-child(2)::before{content:"·";margin:0 .7em}.mast .s span:nth-child(3){flex-basis:100%;text-align:center}
.cover h3{font:400 30px/1.08 var(--display);margin:4px 0 0;text-wrap:balance}
.dek{font-style:italic;color:var(--ink2);margin:0}
.inside{border-top:1px solid var(--ink);padding-top:8px;font-size:13px;line-height:1.4}
.inside b{font:600 10px var(--label);letter-spacing:.14em;text-transform:uppercase;color:var(--accent);display:block;margin-bottom:4px}
.inside ol{margin:0;padding-left:18px}
.kicker{font:600 10px var(--label);letter-spacing:.16em;text-transform:uppercase;color:var(--accent)}
.art h3{font:400 clamp(18px,6.2cqw,26px)/1.1 var(--display);margin:0;text-wrap:balance}.art h3 a,.cover h3 a{color:inherit;text-decoration:none}
.art .ph{max-height:26cqh}
.art .sum{flex:1 1 auto;min-height:0;overflow:hidden}
.byline{font:500 11px var(--label);letter-spacing:.06em;text-transform:uppercase;color:var(--ink2)}
.art p,.letter p{margin:0;font-size:clamp(12px,3.4cqw,15px);line-height:1.5}
.art p:first-of-type::first-letter{font:400 44px/0.8 var(--display);float:left;padding:4px 6px 0 0}
.read{flex:0 0 auto;display:block;font:600 12px var(--label);letter-spacing:.08em;text-transform:uppercase;color:#fff;background:var(--accent);text-decoration:none;padding:9px 12px;text-align:center;border-radius:3px}
.letter h3{font:400 28px/1.1 var(--display);margin:0}
.back{background:var(--desk);color:var(--page)}
.back .folio{color:#b9bcc4;border-color:#b9bcc4}
.back h3{font:400 30px/1.1 var(--display);margin:0;color:var(--bronze)}
.back p{margin:0;font-size:15px;color:#d9dadf}
.back .btn{display:inline-block;border:1px solid var(--bronze);color:var(--bronze);padding:9px 14px;font:600 12px var(--label);letter-spacing:.1em;text-transform:uppercase;text-decoration:none;align-self:flex-start}
.ph{position:relative;width:100%;aspect-ratio:16/9;background:#dcdad3;overflow:hidden;flex:0 0 auto}
.ph img{width:100%;height:100%;object-fit:cover;display:block}
.ph .fb{position:absolute;inset:0;display:none;place-items:center;background:repeating-linear-gradient(135deg,#d6d4cc 0 2px,#e2e0d9 2px 9px)}
.ph.noimg .fb{display:grid}.ph.noimg img{display:none}
.fb span{font:600 12px var(--label);letter-spacing:.12em;text-transform:uppercase;background:#fbfaf7;padding:6px 10px;border:1px solid #b9b7af}
"""


def photo(p, link=None):
    if not p.get("image"):
        return ""
    if link:
        return f'<a href="{E(link)}" target="_blank" rel="noopener" style="display:block">' + photo(p) + "</a>"
    return (f'<div class="ph"><img src="{E(p["image"])}" alt="{E(p["title"])}" loading="lazy" '
            f'onerror="this.parentNode.classList.add(\'noimg\')"><div class="fb"><span>{E(p["source"])}</span></div></div>')


def pages(issue):
    picks, out = issue["picks"], []
    lead = picks[0]
    first = lead["summary"].split(". ")[0].rstrip(".") + "."
    out.append(f'''<div class="page cover" data-density="hard"><div class="pg">
<div class="mast"><div class="t">CEO Inflection</div><div class="s"><span>{E(issue.get("vol",""))}</span><span>{E(issue["label"])}</span><span>Curated by Eric Webb, Founder</span></div></div>
<div class="kicker">Lead story · {E(lead["cat"])}</div><h3><a href="{E(lead["url"])}" target="_blank" rel="noopener">{E(lead["title"])}</a></h3>{photo(lead, lead["url"])}
<p class="dek">{E(first)}</p>
<div class="inside"><b>Inside this issue</b><ol>{"".join(f"<li>{E(p['title'])}</li>" for p in picks[1:])}</ol></div>
</div></div>''')
    intro = "".join(f"<p>{E(t)}</p>" for t in issue.get("intro", []))
    out.append(f'''<div class="page letter"><div class="pg">
<div class="folio"><span>From the chair</span><span>{E(issue["label"])}</span></div>
<h3>A note before you read</h3>{intro}
<p><i>— Eric Webb</i><br><span class="byline">Vistage Chair · Founder, CEO Inflection</span></p>
<div class="folio bot"><span>ceoinflection.com</span><span>2</span></div></div></div>''')
    for i, p in enumerate(picks):
        out.append(f'''<div class="page art"><div class="pg">
<div class="folio"><span>{E(p["cat"])}</span><span>{E(p["source"])}</span></div>
<h3><a href="{E(p["url"])}" target="_blank" rel="noopener">{E(p["title"])}</a></h3><div class="byline">By {E(p["author"])} · {E(p["source"])}</div>{photo(p, p["url"])}
<p class="sum">{E(p["summary"])}</p>
<a class="read" href="{E(p["url"])}" target="_blank" rel="noopener">Read the full article at {E(p["source"])} →</a>
<div class="folio bot"><span>ceoinflection.com</span><span>{i+3}</span></div></div></div>''')
    out.append(f'''<div class="page back" data-density="hard"><div class="pg">
<div class="folio"><span>CEO Inflection</span><span>Back page</span></div>
<h3>Get next month's issue in your inbox</h3>
<p>One email a month. Five reads picked by a Vistage Chair for owners and CEOs of growing companies, each with a short summary so you know which one deserves your time.</p>
<a class="btn" href="{SUBSCRIBE}" target="_blank" rel="noopener">Subscribe at ceoinflection.com</a>
<p style="margin-top:auto;font-size:13px;color:#b9bcc4">Summaries are written by CEO Inflection. Every article belongs to its publisher; each page links to the original.</p>
</div></div>''')
    return out


def edition_html(issue, banner=""):
    pid = E(issue["id"])
    return f'''<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>CEO Inflection {E(issue["label"])}</title>
<meta name="description" content="CEO Inflection, {E(issue["label"])}: five reads for CEOs and owners of growing companies, curated by Eric Webb.">
{'<meta name="robots" content="noindex">' if banner else ''}
{FONTS}<style>{BASE_CSS}
body{{background:var(--desk);padding:14px 12px 18px}}
.bar{{max-width:980px;margin:0 auto 12px;display:flex;flex-wrap:wrap;gap:10px;justify-content:space-between;align-items:center;color:#d9dadf;font:600 12px var(--label);letter-spacing:.1em;text-transform:uppercase}}
.bar a{{color:var(--bronze);text-decoration:none;border:1px solid var(--bronze);border-radius:999px;padding:7px 12px}}
#book{{margin:0 auto}}
.nav{{display:flex;gap:12px;justify-content:center;align-items:center;margin-top:12px;color:#d9dadf;font:600 12px var(--label);letter-spacing:.1em;text-transform:uppercase}}
.nav button{{background:transparent;border:1px solid var(--bronze);color:var(--bronze);border-radius:999px;padding:8px 14px;font:inherit;cursor:pointer}}
.nofx #book{{display:grid;gap:16px;max-width:460px}}.nofx #book .page{{height:620px}}.nofx .nav{{display:none}}
.banner{{max-width:980px;margin:0 auto 10px;background:#fff3c4;color:#5a4a00;font:600 12px var(--label);letter-spacing:.06em;padding:8px 12px;border-radius:6px}}
</style></head><body>
{f'<div class="banner">{E(banner)}</div>' if banner else ''}
<div class="bar"><span>CEO Inflection · {E(issue["label"])}</span>
<span style="display:flex;gap:8px;flex-wrap:wrap"><a href="CEO-Inflection-{pid}.pdf" target="_blank" rel="noopener">Download PDF</a><a href="../../" target="_top">All issues</a><a href="{SUBSCRIBE}" target="_blank" rel="noopener">Subscribe</a></span></div>
<div id="book">{"".join(pages(issue))}</div>
<div class="nav"><button id="prev" aria-label="Previous page">← Prev</button><span id="pnum">Cover</span><button id="next" aria-label="Next page">Next →</button></div>
<script src="https://cdn.jsdelivr.net/npm/page-flip@2.0.7/dist/js/page-flip.browser.js"></script>
<script>
(function(){{
  var book=document.getElementById("book"), n=book.querySelectorAll(".page").length;
  if(!window.St||!St.PageFlip){{document.body.classList.add("nofx");return;}}
  var reduced=matchMedia("(prefers-reduced-motion: reduce)").matches;
  var f=new St.PageFlip(book,{{width:440,height:620,size:"stretch",minWidth:300,maxWidth:480,minHeight:440,maxHeight:680,showCover:true,usePortrait:true,mobileScrollSupport:false,maxShadowOpacity:.45,flippingTime:reduced?1:800}});
  f.loadFromHTML(book.querySelectorAll(".page"));
  f.on("flip",function(e){{var i=e.data;document.getElementById("pnum").textContent=i===0?"Cover":i>=n-1?"Back page":"Page "+(i+1)+" of "+n;}});
  document.getElementById("prev").onclick=function(){{f.flipPrev()}};
  document.getElementById("next").onclick=function(){{f.flipNext()}};
}})();
</script></body></html>'''


def print_html(issue):
    return f'''<!DOCTYPE html><html lang="en"><head><meta charset="utf-8"><title>CEO Inflection {E(issue["label"])} (print)</title>{FONTS}
<style>{BASE_CSS}
@page{{size:6in 8.5in;margin:0}}
body{{background:#fff}}
.page{{width:6in;height:8.5in;page-break-after:always;break-after:page}}
.pg{{padding:.45in .45in .35in}}
.ph .fb{{display:none}}.ph.noimg{{display:none}}
</style></head><body>{"".join(pages(issue))}</body></html>'''


def archive_html(issues):
    latest = issues[0] if issues else None
    items = "".join(
        f'<li><a href="issues/{E(i["id"])}/"><span class="d">{E(i["label"])}</span><span class="t">{E(i["lead"])}</span></a></li>'
        for i in issues)
    hero = (f'''<a class="hero" href="issues/{E(latest["id"])}/"><span class="k">Latest issue · {E(latest["label"])}</span>
<span class="h">{E(latest["lead"])}</span><span class="go">Open the issue →</span></a>''' if latest else
            '<div class="hero"><span class="k">First issue</span><span class="h">The first edition arrives in December 2026.</span></div>')
    return f'''<!DOCTYPE html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>CEO Inflection Issues</title><meta name="description" content="Every issue of CEO Inflection, the monthly reading list for CEOs and owners of growing companies.">{FONTS}
<style>{BASE_CSS}
body{{background:var(--desk);color:var(--light)}}
.mast{{border-bottom:4px double var(--bronze)}}.mast .t{{color:var(--bronze)}}.mast .s{{color:var(--muted)}}
.wrap{{max-width:760px;margin:0 auto;padding:28px 16px 48px;display:grid;gap:22px}}
.mast{{border-bottom:4px double var(--ink)}}
.hero{{display:grid;gap:8px;background:var(--card);border:1px solid var(--line);padding:22px;text-decoration:none;color:var(--light)}}
.hero .k{{font:600 11px var(--label);letter-spacing:.16em;text-transform:uppercase;color:var(--bronze)}}
.hero .h{{font:400 30px/1.1 var(--display);text-wrap:balance}}
.hero .go{{font:600 12px var(--label);letter-spacing:.1em;text-transform:uppercase;color:var(--bronze)}}
h2{{font:600 12px var(--label);letter-spacing:.16em;text-transform:uppercase;color:var(--muted);margin:0;border-bottom:1px solid var(--bronze);padding-bottom:6px}}
ul{{list-style:none;margin:0;padding:0}}
li a{{display:grid;grid-template-columns:140px 1fr;gap:12px;padding:12px 0;border-bottom:1px solid var(--line);text-decoration:none;color:var(--light)}}
li .d{{font:600 12px var(--label);letter-spacing:.08em;text-transform:uppercase;color:var(--bronze)}}
@media (max-width:420px){{li a{{grid-template-columns:1fr;gap:2px}}}}
.sub{{font:600 12px var(--label);letter-spacing:.1em;text-transform:uppercase}}
.sub a{{color:var(--bronze)}}
</style></head><body><div class="wrap">
<div class="mast"><div class="t">CEO Inflection</div><div class="s"><span>Monthly</span><span>Five reads for CEOs of growing companies</span><span>Curated by Eric Webb, Founder</span></div></div>
{hero}
<h2>All issues</h2><ul>{items or '<li style="padding:12px 0;color:var(--muted)">No issues yet.</li>'}</ul>
<p class="sub"><a href="{SUBSCRIBE}" target="_top">Get each issue by email at ceoinflection.com →</a></p>
</div></body></html>'''


def latest_html(issues):
    target = f'../issues/{issues[0]["id"]}/' if issues else "../"
    return f'''<!DOCTYPE html><html lang="en"><head><meta charset="utf-8"><title>CEO Inflection latest issue</title>
<meta http-equiv="refresh" content="0; url={target}"><link rel="canonical" href="{target}"></head>
<body><a href="{target}">Open the latest CEO Inflection issue</a></body></html>'''


def make_pdf(issue_dir, issue_id):
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("Playwright not installed; skipping PDF"); return
    exe = None
    for c in ("/usr/bin/google-chrome", "/usr/bin/chromium", "/usr/bin/chromium-browser"):
        if pathlib.Path(c).exists(): exe = c; break
    with sync_playwright() as p:
        b = p.chromium.launch(executable_path=exe) if exe else p.chromium.launch()
        pg = b.new_page()
        pg.goto((issue_dir / "print.html").as_uri(), wait_until="networkidle")
        pg.pdf(path=str(issue_dir / f"CEO-Inflection-{issue_id}.pdf"), width="6in", height="8.5in", print_background=True)
        b.close()
    print("PDF written for", issue_id)


def main():
    want_pdf = "--pdf" in sys.argv
    only = [a for a in sys.argv[1:] if not a.startswith("--")]
    issues = []
    for f in sorted((ROOT / "issues").glob("*/issue.json"), reverse=True):
        issue = json.loads(f.read_text())
        d = f.parent
        (d / "index.html").write_text(edition_html(issue))
        (d / "print.html").write_text(print_html(issue))
        if want_pdf and (not only or issue["id"] in only):
            make_pdf(d, issue["id"])
        issues.append({"id": issue["id"], "label": issue["label"], "lead": issue["picks"][0]["title"]})
    (ROOT / "index.html").write_text(archive_html(issues))
    (ROOT / "latest").mkdir(exist_ok=True)
    (ROOT / "latest" / "index.html").write_text(latest_html(issues))
    (ROOT / "issues.json").write_text(json.dumps(issues, indent=2))
    # Sample layout (not an issue): sample/issue.json → sample/index.html, marked noindex
    s = ROOT / "sample" / "issue.json"
    if s.exists():
        si = json.loads(s.read_text())
        page = edition_html(si, banner="Sample layout using draft picks. The first real issue replaces this in December.")
        page = page.replace('href="../../"', 'href="../"').replace(f'<a href="CEO-Inflection-{si["id"]}.pdf" target="_blank" rel="noopener">Download PDF</a>', "")
        (ROOT / "sample" / "index.html").write_text(page)
    print(f"Built {len(issues)} issue(s)")


if __name__ == "__main__":
    main()
