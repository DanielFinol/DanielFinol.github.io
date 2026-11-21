#!/usr/bin/env python3
"""Smoke test for index.html. Needs: pip install playwright && playwright install chromium

Usage:  python3 tools/check_page.py [path/to/index.html]
Checks routing, per-language PDF links, expand/collapse, theme and language switching,
the back-to-top button, and that email/phone are not present in the page source.
Contact details are read the same way build_site.py reads them (tools/contact.json or env vars).
"""
import asyncio, json, os, sys
from pathlib import Path
from playwright.async_api import async_playwright

HERE = Path(__file__).resolve().parent
PAGE = Path(sys.argv[1] if len(sys.argv) > 1 else HERE.parent / 'index.html').resolve()
URL = PAGE.as_uri()
results = []
def check(name, ok): results.append((name, bool(ok))); print(('PASS ' if ok else 'FAIL ') + name)

def contact():
    e, p = os.environ.get('FINOL_EMAIL'), os.environ.get('FINOL_PHONE')
    f = HERE / 'contact.json'
    if (not e or not p) and f.exists():
        c = json.loads(f.read_text(encoding='utf-8')); e, p = e or c.get('email'), p or c.get('phone')
    return e, p

async def main():
    src = PAGE.read_text(encoding='utf-8'); e, p = contact()
    if e and p:
        digits = ''.join(ch for ch in p if ch.isdigit())
        check('email not in page source', e not in src)
        check('phone not in page source', p not in src and digits not in src.replace(' ', ''))
    else:
        print('SKIP contact-hiding check (no contact.json / env vars)')
    async with async_playwright() as pw:
        b = await pw.chromium.launch(); errs = []
        ctx = await b.new_context(viewport={'width': 1100, 'height': 800}, color_scheme='dark', locale='en-US')
        pg = await ctx.new_page()
        pg.on('pageerror', lambda x: errs.append(str(x))); pg.on('console', lambda m: errs.append(m.text) if m.type == 'error' else None)
        pdfs = lambda: pg.eval_on_selector_all('a[href$=".pdf"]', 'e=>e.map(x=>x.getAttribute("href"))')
        await pg.goto(URL); await pg.wait_for_timeout(300)
        check('home: two choice cards', await pg.eval_on_selector_all('.choice', 'e=>e.length') == 2)
        check('home: PDFs only for the current language (en)', all('_en' in x for x in await pdfs()) and len(await pdfs()) == 2)
        html = await pg.content()
        check('no mailto:/tel: in DOM before interaction', 'mailto:' not in html.split('<script>')[0] and 'tel:' not in html.split('<script>')[0])
        await pg.click('a[data-v=resume]'); await pg.wait_for_timeout(200)
        check('résumé view via nav', await pg.evaluate('location.hash') == '#resume')
        await pg.click('#all'); check('expand all', await pg.eval_on_selector_all('.sec.open', 'e=>e.length') == await pg.eval_on_selector_all('.sec', 'e=>e.length'))
        await pg.click('.seg button[data-lang=es]'); await pg.wait_for_timeout(200)
        check('language switch updates PDF link (es)', all('_es' in x for x in await pdfs()))
        await pg.click('a[data-v=cv]'); await pg.wait_for_timeout(200)
        total = await pg.eval_on_selector_all('.pin > ul > li', 'e=>e.length')
        await pg.click('.chip[data-topic=neuro]'); await pg.wait_for_timeout(100)
        shown = await pg.eval_on_selector_all('.pin > ul > li', 'e=>e.map(x=>!!x.querySelector("mark.hl"))')
        check('topic filter shows fewer items, each with a highlighted term', 0 < len(shown) < total and all(shown))
        await pg.click('.chip[data-topic=neuro]'); await pg.wait_for_timeout(100)
        check('clicking the topic again restores the full CV', await pg.eval_on_selector_all('.pin > ul > li', 'e=>e.length') == total and await pg.eval_on_selector_all('mark.hl', 'e=>e.length') == 0)
        await pg.click('#all'); await pg.mouse.wheel(0, 3000); await pg.wait_for_timeout(500)
        check('back-to-top visible after scrolling', await pg.evaluate("getComputedStyle(document.getElementById('totop')).visibility") == 'visible')
        await pg.click('#totop'); await pg.wait_for_timeout(1200)
        check('back-to-top returns to top', await pg.evaluate('pageYOffset') == 0)
        await pg.click('#theme'); check('theme toggle sets data-theme', await pg.evaluate('document.documentElement.dataset.theme') in ('light', 'dark'))
        check('no console/page errors', not errs)
        if errs: print(errs)
        await b.close()
    sys.exit(0 if all(ok for _, ok in results) else 1)
asyncio.run(main())
