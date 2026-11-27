# Handoff: danielfinol.github.io (bilingual CV page)

Status as of 2026-11-20. Written so a new session (Claude Code or chat) can continue without the previous conversation.

## What the page is

A single static `index.html` for the GitHub Pages user site (`danielfinol.github.io`). No framework, no build step on GitHub; the file is generated locally from the owner's PDFs by `tools/build_site.py`.

Three views, chosen by the URL hash so the browser back button and shared links work:

| Hash | View | Content |
|---|---|---|
| (none) or `#home` | Landing | Name, title line, centred summary (headline + paragraph), two choice cards (Résumé, Full CV), each with its PDF link |
| `#resume` | Résumé | Short résumé: a Summary block that is always visible, then 5 collapsible sections |
| `#cv` | Full CV | The complete CV: 9 collapsible sections (the full list of items per section) |

Features that exist and must keep working:
- Collapsible sections: each shows title, item count and a short highlights summary; clicking anywhere on it expands the full list. "Expand all / Collapse all" link on the Résumé and CV views.
- English / Spanish toggle (EN, ES). Default: Spanish if the browser's first language starts with "es", otherwise English. The choice is remembered (localStorage, wrapped in try/catch).
- Theme: follows the browser/OS setting; toggle button overrides and is remembered. Dark = true black background with gruvbox colours; light = gruvbox light (cream). If no preference can be detected the page falls back to LIGHT (decision: recruiters and academics mostly read on light systems). This fallback is done in CSS (`prefers-color-scheme`), so it works without JavaScript.
- PDF links: only the PDFs of the currently selected language are shown (on the landing cards and at the top of each view). Switching language swaps them.
- Topic filter (Full CV only): a row of topic buttons (AI, data science, teaching, neuroscience, AI ethics/law/safety, mathematics & optimization, programming). Clicking one shows only the items whose text matches that topic's terms, opens the matching sections, hides the others, shows "n of m items" per section and highlights the matched words (bold with a light underline). Clicking it again, or "Show everything", restores the previous view, including which sections were open. The choice survives a language switch and is cleared when leaving the CV view. Topics and their search terms are in `TOPICS` in `tools/build_site.py`; the build prints the number of matching items per topic for both languages (they should be equal).
- "Back to top" button: bottom-right, appears after scrolling about 700 px, on every view; moves focus to the page title; respects reduced motion.
- Accessibility: section headers are real buttons with `aria-expanded`, panels are regions, keyboard focus is visible, reduced-motion is respected, responsive down to phone width.

## Repository layout (recommended)

```
index.html                              generated; this is what GitHub Pages serves
CV_Daniel_E_Finol_G_en_b.pdf            full CV, English   (linked by the page)
CV_Daniel_E_Finol_G_es_b.pdf            full CV, Spanish
Resume_Daniel_E_Finol_G_en.pdf          résumé, English    (renamed from "résumé_Daniel E. Finol-González_en.pdf")
Resume_Daniel_E_Finol_G_es.pdf          résumé, Spanish
tools/build_site.py                     PDFs -> index.html
tools/template.html                     page design and behaviour (HTML, CSS, JS)
tools/check_page.py                     browser smoke test (optional, needs Playwright)
tools/contact.example.json              copy to tools/contact.json and fill in (never commit)
.gitignore                              must ignore tools/contact.json
```

GitHub Pages serves every file in the repository, including `tools/`. That is fine for the code, but `tools/contact.json` must never be committed.

## How to update the page

1. New CV or résumé PDFs: replace them in the repo root, keeping the file names above.
2. Run `python3 tools/build_site.py` from the repo root. Needs Python 3 and poppler (`pdftohtml`). The script prints the number of items per section for both languages; compare with the previous run, because a changed count usually means a parsing problem.
3. Optionally run `python3 tools/check_page.py` (Playwright), and look at the page in a browser (light, dark, Spanish, phone width, a section expanded).
4. Commit `index.html` and the PDFs.

To change wording or design: hand-written text lives in `tools/build_site.py` (listed below); markup, CSS, JavaScript and the UI labels live in `tools/template.html`. Rebuild after any change.

## How the build works

- `pdftohtml -xml` turns each PDF into positioned text with bold, italic and link markup. The parser walks the lines, detects section headings, bullets and continuation lines, and keeps bold, italic, superscripts and hyperlinks. Only `http(s)` links are kept.
- Inline formatting is passed from Python to the page script with private-use characters: U+E000/E001 bold, U+E002/E003 italic, U+E004 url U+E005 ... U+E006 link, U+E007/E008 superscript, U+E009 starts a nested bullet line (résumé experience). The template's `fmt()` and `li()` turn them into HTML. Do not "clean up" these characters.
- Section headings are matched by their text (`HEADS` for the CV, `RH` for the résumé). If a heading is renamed or a section added in a PDF, update those dictionaries and the matching titles/summaries, otherwise the section is silently dropped or the build fails.
- The résumé parser uses layout rules (headings are larger than 19 pt; bullets start with "•"; in Experience a bold line at the left margin starts a new job). A big redesign of the résumé PDF may need those rules revisited.
- The CV content is shown exactly as in the owner's PDFs (not translated, not reworded). Only titles, highlight summaries and the landing text are written by hand.

### Hand-written text (edit in `tools/build_site.py`)
- `SUMM` (CV section highlights), `RSUMM` (résumé section highlights), `TITLES`, `RTITLES`
- `HOME` (landing headline, paragraph, card descriptions), `RSUB` and `CVSUB` (subtitle lines)
- `TOPICS` (topic button labels and the terms each topic matches)
- UI labels (nav, buttons, "Back to top", download links) are in `tools/template.html`, object `UI`.

## Rules and decisions to keep

- Truthfulness: the owner's CVs are the only source of truth and everything must be 100% truthful. Do not add claims that the CVs do not support. If the owner explicitly asks for a claim that the CVs do not strictly support, say so once and then follow the owner's decision (example: the sentence "Known for explaining complex technical ideas clearly to technical and non-technical audiences" is kept at the owner's explicit request).
- Email and phone must not appear as text anywhere in the page source. The page builds them at run time from reversed character codes, and only turns them into `mailto:` / `tel:` links on interaction. They come from `tools/contact.json` or the environment variables `FINOL_EMAIL` and `FINOL_PHONE`. Never write them into the repository, this file, commit messages or code. Limit: the PDFs themselves contain them in plain text.
- Name is written "Daniel E. Finol-González" on the page, in both languages.
- Visual direction: legible, clear, elegant in both themes; dark theme absolute black with gruvbox-like colours; serif body text (Palatino/Georgia stack), system sans for controls.
- Every text change is made in both languages. The owner reads and approves the wording; they iterate in small steps. The Spanish landing text is adapted from the English, not a literal translation.
- Landing text history (for context): the owner asked for a summary that is attractive to employers in academia and industry but honest. The current paragraph states: led a funded research project on machine learning, co-authored papers on AI and law, taught Python and data science in Chile, a year at Ipsos, recent AI-safety and generative-AI training, bilingual (native Spanish, English C2).

## Things in the PDFs the owner may want to fix (not page bugs)

- English CV: the master's average reads "(97,8%)" with a decimal comma; the Spanish CV uses 97.8.
- The résumé PDFs say a master's average of 19.56/20, while the CVs now say 19.6/20.
- The hand-written page text says "14 years" of graduate teaching and a 98% average (owner's decision, 2026-11-27). The PDFs still say 13 years (résumé Summary) and 97.8%, and the page shows the PDF-derived text as is, so those spots still read 13 / 97.8 until the PDFs are updated.
- All four PDFs contain the owner's email and phone in plain text, so bots can read them from the PDFs even though the page hides them.
- The résumé PDF Summary paragraph still carries wording the owner chose to keep ("published machine-learning research", "Known for explaining ..."); the interactive résumé mirrors the PDF.

## Testing notes

- Chromium and Playwright worked in the previous environment. Useful checks: each view in light and dark, Spanish, a 390 px wide viewport, a section expanded, scroll far down and use the back-to-top button, navigate with the hash links and the browser back button.
- `tools/check_page.py` automates: contact details not in the source, PDF links per language, routing, expand all, language and theme switching, back-to-top.
- The last build is byte-identical to the file delivered in the chat on 2026-11-20 and to the project copy `Curriculum/web/index.html` as far as inspected.

## Possible next steps (suggestions only, nothing is decided)

- An "open to ..." line on the landing page (needs the owner's target roles, academia or industry).
- Limit the back-to-top button to the CV views, if the owner prefers.
- Print stylesheet for the Résumé view.
