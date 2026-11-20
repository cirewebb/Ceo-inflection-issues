# CEO Inflection issues

Page-turning editions and PDFs of the CEO Inflection monthly newsletter, published with GitHub Pages.

- `index.html`: archive of every issue
- `latest/`: always opens the newest issue (use this address in the ceoinflection.com embed)
- `issues/<YYYY-MM>/issue.json`: one issue's content; `build.py` renders the page and PDF from it
- `sample/`: layout sample using draft picks (not indexed by search engines)

Rebuild after adding an issue: `python3 build.py --pdf <YYYY-MM>`
