"""Builds index.html (English) and fr/index.html (French) from page.html and the string files.

Run from anywhere: python3 _src/build.py. Pages publishes the built files; _src itself isn't served.
"""
import html
import json
import re
from pathlib import Path

SRC = Path(__file__).parent
ROOT = SRC.parent


def icon(name):
    return f'<svg class="i" aria-hidden="true"><use href="#i-{name}"/></svg>'


def copy_btn(s, text):
    return (f'<button class="copy" type="button" data-copy="{html.escape(text)}">'
            f'{icon("copy")}<span>{s["copy"]}</span></button>')


def code(s, text):
    return f'<div class="copybox"><code>{html.escape(text)}</code>{copy_btn(s, text)}</div>'


def blocks(s):
    """The repeated parts of the page, built from the lists in the string file."""
    return {
        "alt_lang_upper": s["alt_lang"].upper(),
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
            f'<a href="{path}" hreflang="{code_}" lang="{code_}" data-lang-link'
            + (' aria-current="true"' if code_ == s["lang"] else "") + f">{name}</a>"
            for code_, path, name in (("en", "/", "English"), ("fr", "/fr/", "Français"))),
        "js_strings": json.dumps({k: s[k] for k in (
            "lang", "alt_lang", "theme_label", "theme_auto", "theme_light", "theme_dark",
            "of", "copy", "copied", "play", "pause")} | {"tour": s["tour"]}, ensure_ascii=False).replace("</", "<\\/"),
    }


def render(template, s):
    values = {k: v for k, v in s.items() if isinstance(v, str)} | blocks(s)
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
    en = json.loads((SRC / "en.json").read_text())
    fr = json.loads((SRC / "fr.json").read_text())
    # Both languages must say the same things.
    assert en.keys() == fr.keys(), en.keys() ^ fr.keys()
    for k in ("tour", "features", "steps", "using", "faq", "privacy", "footer_links", "credits", "facts"):
        assert len(en[k]) == len(fr[k]), k
    for s in (en, fr):
        out = ROOT / s["path"].strip("/") / "index.html"
        out.parent.mkdir(exist_ok=True)
        out.write_text(render(template, s))
        print("wrote", out.relative_to(ROOT))


if __name__ == "__main__":
    main()
