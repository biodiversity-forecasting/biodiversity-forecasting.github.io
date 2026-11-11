#!/usr/bin/env python3
"""Byggjer nettsida til Senter for naturprognosar (CBF).

Bruk:
    python build.py                 # byggjer til _site/
    python build.py --serve         # byggjer og startar ein lokal testserver på http://localhost:8000
    python build.py --explicit-index  # lenkjer til .../index.html (for førehandsvising utan webserver)

Innhald ligg i content/<språk>/*.md, felles data i data/*.yaml, utsjånad i templates/ og static/.
Krev berre Python 3 med pakkane markdown, jinja2 og pyyaml.
"""
import argparse
import datetime as dt
import http.server
import os
import posixpath
import re
import shutil
import socketserver
from pathlib import Path

import jinja2
import markdown
import yaml

import nva

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "_site"
FRONT_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n?(.*)$", re.S)


def load_yaml(path):
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def md(text, lang="nn"):
    quotes = {"left-double-quote": "«", "right-double-quote": "»"} if lang != "en" else {}
    return markdown.markdown(
        text or "",
        extensions=["extra", "sane_lists", "smarty", "toc"],
        extension_configs={"smarty": {"substitutions": quotes}},
    )


def read_page(path, lang):
    raw = path.read_text(encoding="utf-8")
    m = FRONT_RE.match(raw)
    meta, body = (yaml.safe_load(m.group(1)) or {}, m.group(2)) if m else ({}, raw)
    rel = path.relative_to(ROOT / "content" / lang).with_suffix("")
    parts = list(rel.parts)
    if parts[-1] == "index":
        parts = parts[:-1]
    slug = "/".join(parts)
    url = f"/{lang}/" + (slug + "/" if slug else "")
    page = dict(meta)
    page.update(lang=lang, slug=slug, url=url, source=str(path.relative_to(ROOT)),
                body_html=md(body, lang), layout=meta.get("layout", "page"),
                key=meta.get("key", slug or "home"))
    if isinstance(page.get("date"), (dt.date, dt.datetime)):
        page["date"] = page["date"] if isinstance(page["date"], dt.date) else page["date"].date()
    page["section"] = parts[0] if len(parts) > 1 else None
    return page


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--explicit-index", action="store_true")
    ap.add_argument("--serve", action="store_true")
    ap.add_argument("--variant", choices=["dark", "light"], default=None)
    ap.add_argument("--nva-sample", default=None, help="JSON-fil med NVA-svar (berre til testing)")
    ap.add_argument("--fonts", choices=["local", "google"], default=None,
                    help="local = sjølvhosta skrifter (standard), google = Google Fonts (berre til førehandsvising)")
    args = ap.parse_args()

    site = load_yaml(ROOT / "site.yaml")
    data = {p.stem: load_yaml(p) for p in sorted((ROOT / "data").glob("*.yaml"))}
    langs = site["languages"]
    fonts = args.fonts or site.get("fonts", "local")
    variant = args.variant or site.get("variant", "dark")

    pages = []
    for lang in langs:
        for p in sorted((ROOT / "content" / lang).rglob("*.md")):
            pg = read_page(p, lang)
            if not pg.get("draft"):
                pages.append(pg)

    # Publikasjonar frå NVA. Utan publikasjonar vert publikasjonssida halden skjult.
    publications = nva.load((site.get("nva") or {}).get("projects"), args.nva_sample)
    if not publications:
        pages = [p for p in pages if p["layout"] != "publications"]
    print(f"Publikasjonar frå NVA: {len(publications)}")

    by_key = {}
    for pg in pages:
        by_key.setdefault(pg["key"], {})[pg["lang"]] = pg

    def section_pages(lang, section):
        items = [p for p in pages if p["lang"] == lang and p["section"] == section]
        return sorted(items, key=lambda p: (p.get("order", 999), -(p["date"].toordinal() if p.get("date") else 0)))

    def news(lang, limit=None):
        sec = site["news_section"][lang]
        items = [p for p in pages if p["lang"] == lang and p["section"] == sec and p.get("date")]
        items.sort(key=lambda p: p["date"], reverse=True)
        return items[:limit] if limit else items

    env = jinja2.Environment(loader=jinja2.FileSystemLoader(ROOT / "templates"),
                             autoescape=jinja2.select_autoescape(["html"]),
                             trim_blocks=True, lstrip_blocks=True)
    env.filters["md"] = lambda s: jinja2.utils.markupsafe.Markup(md(s))
    env.filters["mdi"] = lambda s: jinja2.utils.markupsafe.Markup(
        re.sub(r"^<p>(.*)</p>$", r"\1", md(s).strip(), flags=re.S))

    def fmt_date(d, lang):
        months = site["months"][lang]
        return f"{d.day}. {months[d.month - 1]} {d.year}" if lang != "en" else f"{d.day} {months[d.month - 1]} {d.year}"

    if OUT.exists():
        shutil.rmtree(OUT)
    shutil.copytree(ROOT / "static", OUT)

    base_url = (site.get("base_url") or "").rstrip("/")
    for pg in pages:
        here = pg["url"]

        def rel(target, _here=here):
            """Relativ lenkje frå denne sida, så sida fungerer same kvar ho ligg."""
            if re.match(r"^(https?:|mailto:|tel:|#)", target):
                return target
            frag = ""
            if "#" in target:
                target, frag = target.split("#", 1)
                frag = "#" + frag
            r = posixpath.relpath(target, _here if _here.endswith("/") else posixpath.dirname(_here))
            if target.endswith("/"):
                r = (r + "/") if r != "." else "./"
                if args.explicit_index:
                    r += "index.html"
            return r + frag

        def page_url(key, lang=pg["lang"]):
            t = by_key.get(key, {}).get(lang)
            return rel(t["url"]) if t else "#"

        # I innhaldsfilene skriv ein absolutte stiar (/img/..., /nn/bli-med/); dei vert gjort relative her
        pg = dict(pg, body_html=re.sub(r'(src|href)="(/[^"/][^"]*|/)"',
                                       lambda m, r=rel: f'{m[1]}="{r(m[2])}"', pg["body_html"]))
        def has_page(key, lang=pg["lang"]):
            return lang in by_key.get(key, {})

        # <!-- mørkt band --> … <!-- /mørkt band --> i innhaldet gjev eit djupblått band over heile breidda
        pg["body_html"] = pg["body_html"].replace(
            "<!-- mørkt band -->", '</div></article><section class="band-dark dark-section"><div class="wrap"><div class="prose">'
        ).replace(
            "<!-- /mørkt band -->", '</div></div></section><article class="wrap prose-wrap"><div class="prose">')
        ctx = dict(nva_sample=bool(args.nva_sample), publications=publications, variant=variant, has_page=has_page, site=site, data=data, page=pg, lang=pg["lang"], ui=site["ui"][pg["lang"]],
                   rel=rel, page_url=page_url, translations=by_key.get(pg["key"], {}),
                   section_pages=section_pages, news=news, fmt_date=fmt_date, fonts=fonts,
                   year=dt.date.today().year, base_url=base_url)
        html = env.get_template(pg["layout"] + ".html").render(**ctx)
        dest = OUT / here.strip("/") / "index.html"
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(html, encoding="utf-8")

    # Rotsida sender vidare til rett språk
    first = langs[0]
    root_ctx = dict(site=site, fonts=fonts, explicit=args.explicit_index, langs=langs, first=first)
    (OUT / "index.html").write_text(env.get_template("root.html").render(**root_ctx), encoding="utf-8")
    (OUT / "404.html").write_text(env.get_template("404.html").render(**root_ctx), encoding="utf-8")
    (OUT / ".nojekyll").write_text("")
    if site.get("domain"):
        (OUT / "CNAME").write_text(site["domain"].strip() + "\n")

    if base_url:
        rows = []
        for pg in pages:
            alts = "".join(
                f'<xhtml:link rel="alternate" hreflang="{l}" href="{base_url}{t["url"]}"/>'
                for l, t in by_key[pg["key"]].items())
            rows.append(f"<url><loc>{base_url}{pg['url']}</loc>{alts}</url>")
        (OUT / "sitemap.xml").write_text(
            '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" '
            'xmlns:xhtml="http://www.w3.org/1999/xhtml">' + "".join(rows) + "</urlset>\n", encoding="utf-8")
        (OUT / "robots.txt").write_text(f"User-agent: *\nAllow: /\nSitemap: {base_url}/sitemap.xml\n")

    print(f"Bygde {len(pages)} sider til {OUT.relative_to(ROOT)}/")

    if args.serve:
        os.chdir(OUT)
        with socketserver.TCPServer(("", 8000), http.server.SimpleHTTPRequestHandler) as httpd:
            print("Testserver: http://localhost:8000  (Ctrl+C for å stoppa)")
            httpd.serve_forever()


if __name__ == "__main__":
    main()
