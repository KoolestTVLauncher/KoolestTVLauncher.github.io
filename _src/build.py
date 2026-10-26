"""Builds index.html (English), fr/index.html (French) and fa/index.html (Persian, right to left)
from page.html and the string files.

Run from anywhere: python3 _src/build.py. Pages publishes the built files; _src itself isn't served.
"""
import html
import json
import re
from pathlib import Path

SRC = Path(__file__).parent
ROOT = SRC.parent
SITE = "https://koolesttvlauncher.github.io"
# Code, name in itself, top-bar label. English first: it's the x-default.
LANGS = (("en", "English", "EN"), ("fr", "Français", "FR"), ("fa", "فارسی", "فا"))


def icon(name):
    return f'<svg class="i" aria-hidden="true"><use href="#i-{name}"/></svg>'


def copy_btn(s, text):
    return (f'<button class="copy" type="button" data-copy="{html.escape(text)}">'
            f'{icon("copy")}<span>{s["copy"]}</span></button>')


def code(s, text):
    return f'<div class="copybox"><code dir="ltr">{html.escape(text)}</code>{copy_btn(s, text)}</div>'


def blocks(s, all_s):
    """The repeated parts of the page, built from the lists in the string file."""
    others = [(c, n, short) for c, n, short in LANGS if c != s["lang"]]
    return {
        "alternates": "\n".join(
            f'<link rel="alternate" hreflang="{c}" href="{SITE}{all_s[c]["path"]}">' for c, _, _ in LANGS),
        "lang_chips": "".join(
            f'<a class="chip" href="{all_s[c]["path"]}" hreflang="{c}" lang="{c}" data-lang-link title="{n}">{short}</a>'
            for c, n, short in others),
        "facts_list": "".join(f"<li>{icon('check')}{f}</li>" for f in s["facts"]),
        "tour_buttons": "".join(
            f'<button role="tab" type="button" aria-selected="false" tabindex="-1">'
            f'<img src="/img/{t["img"]}-sm.webp" alt="" loading="lazy" width="480" height="270"><span>{t["title"]}</span></button>'
            for t in s["tour"]),
        "features_list": "".join(
            f'<li><span class="ic">{icon(f["icon"])}</span><h3>{f["title"]}</h3><p>{f["text"]}</p></li>'
            for f in s["features"]),
        "steps_list": "".join(f'<li><h3>{st["title"]}</h3>{st["html"]}</li>' for st in s["steps"]),
        "using_rows": "".join(f"<tr><td>{a}</td><td>{b}</td></tr>" for a, b in s["using"]),
        "faq_list": "".join(
            f'<details><summary>{q["q"]}{icon("plus")}</summary><div>{q["a"]}</div></details>' for q in s["faq"]),
        "privacy_list": "".join(f"<li>{p}</li>" for p in s["privacy"]),
        "footer_links_list": "".join(f'<li><a href="{u}">{t}</a></li>' for t, u in s["footer_links"]),
        "credits_list": "".join(f"<li>{c}</li>" for c in s["credits"]),
        "lang_seg": "".join(
            f'<a href="{all_s[c]["path"]}" hreflang="{c}" lang="{c}" data-lang-link'
            + (' aria-current="true"' if c == s["lang"] else "") + f">{n}</a>"
            for c, n, _ in LANGS),
        # The banner offering another language is written in that language, so each page carries the others' offers.
        "js_strings": json.dumps({k: s[k] for k in (
            "lang", "dir", "theme_label", "theme_auto", "theme_light", "theme_dark",
            "of", "copy", "copied", "play", "pause")} | {"tour": s["tour"]} | {"suggest": {
                c: {"path": all_s[c]["path"], "dir": all_s[c]["dir"], "text": all_s[c]["suggest_text"], "go": all_s[c]["suggest_go"]}
                for c, _, _ in others}}, ensure_ascii=False).replace("</", "<\\/"),
    }


def render(template, s, all_s):
    values = {k: v for k, v in s.items() if isinstance(v, str)} | blocks(s, all_s)
    out = template
    # Repeat until no placeholders are left: some strings carry their own {{code:...}}.
    for _ in range(3):
        out = re.sub(r"\{\{code:([^}]*)\}\}", lambda m: code(s, html.unescape(m.group(1))), out)
        out = re.sub(r"\{\{copy_btn:([^}]*)\}\}", lambda m: copy_btn(s, m.group(1)), out)
        out = re.sub(r"\{\{(\w+)\}\}", lambda m: values[m.group(1)], out)
    left = re.findall(r"\{\{[^}]*\}\}", out)
    assert not left, f"unfilled placeholders: {left}"
    return out


def main():
    template = (SRC / "page.html").read_text()
    all_s = {c: json.loads((SRC / f"{c}.json").read_text()) for c, _, _ in LANGS}
    en = all_s["en"]
    # Every language must say the same things.
    for c, s in all_s.items():
        assert s["lang"] == c and s["dir"] in ("ltr", "rtl"), c
        assert en.keys() == s.keys(), (c, en.keys() ^ s.keys())
        for k in ("tour", "features", "steps", "using", "faq", "privacy", "footer_links", "credits", "facts"):
            assert len(en[k]) == len(s[k]), (c, k)
        assert [t["img"] for t in s["tour"]] == [t["img"] for t in en["tour"]], c
    for s in all_s.values():
        out = ROOT / s["path"].strip("/") / "index.html"
        out.parent.mkdir(exist_ok=True)
        out.write_text(render(template, s, all_s))
        print("wrote", out.relative_to(ROOT))


if __name__ == "__main__":
    main()
