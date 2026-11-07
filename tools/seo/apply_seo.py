"""Poprawki SEO z audytu 2026-11-07 dla statycznej strony public/akumulatory-tarnow.

Uruchomienie (z katalogu repo):  python tools/seo/apply_seo.py
Skrypt jest idempotentny: kolejne uruchomienie daje ten sam wynik.
Wymaga: Python 3.11+, beautifulsoup4 (do odczytu), Pillow (obrazy).
"""
from __future__ import annotations

import collections
import html
import json
import re
import sys
from urllib.parse import unquote
from pathlib import Path

from bs4 import BeautifulSoup

sys.path.insert(0, str(Path(__file__).parent))
from site_data import (BRAND, EMAIL, FACEBOOK, FREE_SERVICES, LOCATIONS, PAGES, PHONE, PHONE_DISPLAY,  # noqa: E402
                       PREFIX, PROD_ORIGIN, SERVICES, SUFFIX)

REPO = Path(__file__).resolve().parents[2]
SITE = REPO / "public" / "akumulatory-tarnow"
SEO_START, SEO_END = "<!--seo-->", "<!--/seo-->"
ACRONYMS = {"UPS", "AGM", "EFB", "OE", "ASO"}
# kategorie demo z modułu bloga ("Kategoria 1", "Sub Category 1/2"): noindex, poza sitemapą, stare adresy -> /porady/
DEMO_BLOG = ("porady/kategoria-1/", "porady/sub-category-1/", "porady/sub-category-2/")
esc = lambda s: html.escape(s, quote=True)  # noqa: E731


# ---------------------------------------------------------------- helpers
def read(p: Path) -> str:
    return p.read_text(encoding="utf-8")


def write(p: Path, text: str) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8", newline="\n")


def rel(p: Path) -> str:
    """Ścieżka strony względem katalogu głównego, np. 'oferta/' albo ''."""
    r = p.relative_to(SITE).as_posix()
    if r == "index.html":
        return ""
    if r.endswith("/index.html"):
        return r[: -len("index.html")]
    return r


def prod_url(path: str) -> str:
    return f"{PROD_ORIGIN}/{path}"


def is_stub(text: str) -> bool:
    return 'http-equiv="refresh"' in text[:600]


def sentence(name: str) -> str:
    if not name.isupper():
        return name
    words = name.split()
    out = []
    for i, w in enumerate(words):
        if w.strip(",/") in ACRONYMS:
            out.append(w)
        else:
            low = w.lower()
            out.append(low.capitalize() if i == 0 else low)
    return " ".join(out)


def plural(n: int) -> str:
    if n == 1:
        return "1 produkt"
    if n % 10 in (2, 3, 4) and n % 100 not in (12, 13, 14):
        return f"{n} produkty"
    return f"{n} produktów"


def fit_title(main: str, limit: int = 60) -> str:
    """Sufiks marki tylko wtedy, gdy cały tytuł mieści się w limicie znaków."""
    main = main.strip()
    return main + SUFFIX if len(main + SUFFIX) <= limit else main


def fit_desc(*candidates: str, limit: int = 160) -> str:
    """Pierwszy wariant opisu, który mieści się w limicie; w ostateczności ostatni."""
    for c in candidates:
        if len(c) <= limit:
            return c
    return candidates[-1]


def set_title(text: str, title: str) -> str:
    return re.sub(r"<title>.*?</title>", f"<title>{esc(title)}</title>", text, count=1, flags=re.S)


def set_description(text: str, desc: str) -> str:
    tag = f'<meta content="{esc(desc)}" name="description"/>'
    if re.search(r'<meta content="[^"]*" name="description"/>', text):
        return re.sub(r'<meta content="[^"]*" name="description"/>', lambda m: tag, text, count=1)
    return text.replace("</title>", "</title>" + tag, 1)


def set_h1(text: str, h1: str) -> str:
    return re.sub(r"<h1>.*?</h1>", f"<h1>{esc(h1)}</h1>", text, count=1, flags=re.S)


def get_title(text: str) -> str:
    m = re.search(r"<title>(.*?)</title>", text, flags=re.S)
    return html.unescape(m.group(1)) if m else ""


def get_desc(text: str) -> str:
    m = re.search(r'<meta content="([^"]*)" name="description"/>', text)
    return html.unescape(m.group(1)) if m else ""


def breadcrumbs(text: str) -> list[tuple[str, str]]:
    m = re.search(r'<nav aria-label="Ścieżka nawigacji" class="breadcrumbs">(.*?)</nav>', text, flags=re.S)
    if not m:
        return []
    out = []
    for a in re.finditer(r'<a href="([^"]+)">(.*?)</a>|<span aria-current="page">(.*?)</span>', m.group(1)):
        if a.group(1):
            out.append((html.unescape(re.sub("<.*?>", "", a.group(2))), a.group(1)))
        else:
            out.append((html.unescape(re.sub("<.*?>", "", a.group(3))), ""))
    return out


def to_path(href: str) -> str:
    return href[len(PREFIX):] if href.startswith(PREFIX) else href.lstrip("/")


# ---------------------------------------------------------------- data
catalog = json.loads(read(SITE / "assets" / "catalog-data.json"))
products = {p["id"]: p for p in catalog["products"]}
categories = {c["id"]: c for c in catalog["categories"]}
brands = {b["id"]: b for b in catalog["brands"]}
brand_slug = {}
for d in (SITE / "brand").iterdir():
    m = re.match(r"(\d+)-(.+)", d.name)
    if m:
        brand_slug[int(m.group(1))] = m.group(2)
for bid in brands:
    brand_slug.setdefault(bid, re.sub(r"[^a-z0-9]+", "-", brands[bid]["name"].lower()).strip("-"))


def cat_chain(cid: int) -> list[dict]:
    chain = []
    while cid in categories:
        chain.append(categories[cid])
        cid = categories[cid].get("parent")
    chain.reverse()
    # wspólny korzeń drzewa nazywa się "Sklep" – liczy się dział pod nim (AKUMULATORY SAMOCHODOWE, PROSTOWNIKI...)
    trimmed = [c for c in chain if c["name"].strip().lower() != "sklep"]
    return trimmed or chain


def cat_title(cid: int) -> str:
    names = [c["name"] for c in cat_chain(cid)]
    root = sentence(names[0])
    rest = [n.strip() for n in names[1:]]
    do = [n for n in rest if n.lower().startswith("do ")]
    others = []
    for n in rest:
        if n.lower().startswith("do "):
            continue
        # podkategorie marek nazywają się np. "AKUMULATORY SAMOCHODOWE VIKING" – nazwa działu jest już w tytule
        if n.lower().startswith(names[0].strip().lower()):
            n = n[len(names[0].strip()):].strip()
        if n:
            others.append(n)
    if do:
        return " ".join(["Akumulatory", *others, do[0].lower()])
    if not others:
        return root
    return f"{' '.join(others)} – {root[0].lower() + root[1:]}"


name_count = collections.Counter(c["name"].strip().lower() for c in categories.values())
cat_by_path = {to_path(c["url"]): c for c in categories.values()}
title_count = collections.Counter(p["title"].strip().lower() for p in products.values())
title_groups: dict[str, list[dict]] = collections.defaultdict(list)
for _p in products.values():
    title_groups[_p["title"].strip().lower()].append(_p)


def polarity(p: dict) -> str:
    b = (p.get("filters") or {}).get("biegun", "")
    return {"Prawy +": "prawy plus", "Lewy +": "lewy plus"}.get(b.strip(), "")


def disambiguator(p: dict) -> str:
    """Dopisek do tytułu produktu, gdy kilka produktów ma tę samą nazwę.

    Biegun z filtra, jeśli rozróżnia całą grupę; inaczej indeks producenta z danych
    (w części par filtr podaje ten sam biegun mimo indeksów P+/L+ – do potwierdzenia u klienta).
    """
    group = title_groups[p["title"].strip().lower()]
    pols = [polarity(g) for g in group]
    if all(pols) and len(set(pols)) == len(group):
        return polarity(p)
    refs = [(g.get("reference") or "").strip() for g in group]
    if all(refs) and len(set(refs)) == len(group):
        return p["reference"].strip()
    return polarity(p)


def product_kind(p: dict) -> str:
    roots = {cat_chain(c)[0]["id"] for c in p["categories"] if c in categories}
    names = " ".join(categories[r]["name"].lower() for r in roots)
    if "akumulator" in names or "baterie" in names:
        return "battery"
    if "prostowniki" in names:
        return "charger"
    if "rozruchowe" in names:
        return "booster"
    if "ups" in names:
        return "ups"
    return "battery"


# ---------------------------------------------------------------- product pages present in the build
product_pages: dict[int, Path] = {}
for p in products.values():
    page = SITE / to_path(p["url"]) / "index.html"
    if page.exists():
        product_pages[p["id"]] = page


def brand_categories(name: str, items: list[dict]) -> list[tuple[int, int]]:
    """Kategorie marki z liczbą jej produktów: kategorie nazwane marką, a gdy ich brak – najgłębsze kategorie produktów.

    Wstęp marki nie kopiuje już opisu jednego produktu (był powielony na stronach produktów i nie pasował do całej marki).
    """
    named = {c for p in items for c in p["categories"] if c in categories and categories[c]["name"].strip().lower().startswith(name.lower()[:4])}
    if not named:
        real = lambda p: [c for c in p["categories"] if c in categories and categories[c]["name"].strip().lower() != "sklep"]  # noqa: E731
        named = {max(real(p), key=lambda c: len(cat_chain(c))) for p in items if real(p)}
    counted = [(c, sum(1 for p in items if c in p["categories"])) for c in named]
    return sorted(counted, key=lambda x: (-x[1], cat_title(x[0])))


# ---------------------------------------------------------------- page shells for new pages
def shell(template: Path) -> tuple[str, str]:
    t = read(template)
    t = re.sub(re.escape(SEO_START) + ".*?" + re.escape(SEO_END), "", t, flags=re.S)
    head_part = t[: t.index('<main id="main">')]
    tail = t[t.index("</main>") + len("</main>"):]
    return head_part, tail


def card(p: dict) -> str:
    f = p.get("filters") or {}
    params = " · ".join(x for x in (f"{f['ah']} Ah" if f.get("ah") else "", f"{f['prad']} A" if f.get("prad") else "") if x)
    return (f'<a class="product-card" data-product-id="{p["id"]}" href="{p["url"]}"><div class="product-card-image">'
            f'<img alt="{esc(p["title"])}" class="" decoding="async" loading="lazy" src="{p["image"]}"/></div>'
            f'<div class="product-card-copy"><span class="product-brand">{esc(p.get("brand") or "")}</span>'
            f'<h2>{esc(p["title"])}</h2><p class="card-parameters">{params}</p></div>'
            f'<span aria-hidden="true" class="card-arrow">↗</span></a>')


def crumbs_html(items: list[tuple[str, str]]) -> str:
    parts = []
    for name, href in items:
        parts.append(f'<a href="{href}">{esc(name)}</a>' if href else f'<span aria-current="page">{esc(name)}</span>')
    return '<nav aria-label="Ścieżka nawigacji" class="breadcrumbs">' + '<span aria-hidden="true">/</span>'.join(parts) + "</nav>"


PHOTO = f'{PREFIX}assets/responsive/hero-2-7e11b8c392cdbffb3fc476fea7c3175d_1-full.webp'


def build_brand_pages() -> dict[str, dict]:
    head_part, tail = shell(SITE / "marki" / "index.html")
    meta = {}
    by_brand = collections.defaultdict(list)
    for p in products.values():
        if p.get("brandId") in brands and p["id"] in product_pages:
            by_brand[p["brandId"]].append(p)
    for bid, items in by_brand.items():
        b = brands[bid]
        slug = brand_slug[bid]
        kinds = collections.Counter(product_kind(p) for p in items)
        kind = kinds.most_common(1)[0][0]
        noun = {"battery": "akumulatory", "charger": "prostowniki i ładowarki", "booster": "urządzenia rozruchowe", "ups": "zasilacze awaryjne UPS"}[kind]
        name = b["name"]
        if kind == "battery":
            h1, title = f"Akumulatory {name}", f"Akumulatory {name} Tarnów | {BRAND}"
        else:
            h1, title = f"{name} – {noun}", f"{name} – {noun}, Tarnów"
            if len(title + f" | {BRAND}") <= 60:
                title += f" | {BRAND}"
        desc = (f"{name}: {plural(len(items))} w ofercie Pogotowia Akumulatorowego. "
                f"Zapytaj o dostępność w sklepach w Tarnowie (Krakowska 150, Giełdowa 5) i Radłowie: {PHONE_DISPLAY}.")
        extra = ""
        if name.upper() == "BANNER":
            extra = "<p>Posiadamy status <strong>Autoryzowanej Stacji Obsługi Akumulatorów Banner</strong>.</p>"
        # widoczna lista kategorii marki (blok .subcategory-links jest na tej stronie ukryty przez CSS: .catalog-site .subcategory-links)
        cats = brand_categories(name, items)[:8]
        cat_list = " · ".join(f'<a href="{categories[c]["url"]}">{esc(cat_title(c))}</a> ({n})' for c, n in cats)
        montaz = " Przy odbiorze akumulatora w sklepie stacjonarnym montaż jest bezpłatny." if kind == "battery" else ""
        sorted_items = sorted(items, key=lambda p: (p["title"], p["id"]))
        main = (f'<main id="main"><div class="page-top visual-page-top" style=\'--page-photo:url("{PHOTO}")\'>'
                + crumbs_html([("Strona główna", PREFIX), ("Marki", f"{PREFIX}marki/"), (name, "")])
                + f'<h1>{esc(h1)}</h1></div>'
                # tekst w jasnej karcie jak na stronach usług (na ciemnym zdjęciu kontrast wynosił ok. 2,2:1)
                + '<div class="service-copy brand-copy"><div class="prose">'
                + extra
                + f'<p>{esc(name)} w naszej ofercie: {plural(len(items))}. Zapytaj o dostępność w sklepach w Tarnowie i Radłowie albo zadzwoń: '
                  f'<a href="tel:{PHONE}">{PHONE_DISPLAY}</a>.{montaz}</p>'
                + (f"<p>Kategorie: {cat_list}</p>" if cat_list else "")
                + "</div></div>"
                + f'<div class="catalog-results brand-results"><div class="results-toolbar"><p>{plural(len(items))}</p>'
                  f'<a class="text-link" data-filter-link="" href="{PREFIX}oferta/?marka={bid}" rel="nofollow">Filtruj w katalogu ↗</a></div>'
                + '<div class="product-grid">' + "".join(card(p) for p in sorted_items) + "</div></div></main>")
        page = head_part + main + tail
        page = set_title(page, title)
        page = set_description(page, desc)
        out = SITE / "marki" / slug / "index.html"
        write(out, page)
        meta[f"marki/{slug}/"] = {"brand_id": bid, "name": name, "count": len(items)}
    return meta


# ---------------------------------------------------------------- collection pages (technologia i pojemność)
# Katalog jest ułożony według działu > marki > serii, więc akumulatory AGM czy 74 Ah są rozrzucone po wielu gałęziach.
# Strony zbiorcze odpowiadają na frazy z DataForSEO (2026-11-07): akumulator agm 8100, efb 2400, start-stop 1600,
# akumulator 74ah 5400, 100ah 4400, 60ah 2900 wyszukiwań/mies. Zasady wymiany AGM/EFB: VARTA, "EFB and AGM differences"
# oraz "Changing a start-stop battery" (varta-automotive.com).
GROUP_SUFFIX = {"do-aut-osobowych": "do aut osobowych", "do-aut-ciezarowych-dostawczych-": "do aut ciężarowych i dostawczych",
                "akumulatory-motocyklowe": "do motocykli", "akumulatory-marine-": "marine", "akumulatory-zelowe": "żelowe",
                "akumulatory-rolnicze-": "do maszyn rolniczych", "akumulatory-do-kosiarek": "do kosiarek", "baterie-trakcyjne": "trakcyjne"}
KOD = f'<a href="{PREFIX}uslugi/kodowanie-akumulatora/">kodowanie akumulatora</a>'
PODTRZ = f'<a href="{PREFIX}uslugi/wymiana-akumulatora-z-podtrzymaniem-elektroniki/">wymianę z podtrzymaniem elektroniki</a>'
COLL_NAV_PAGES = ("oferta/", "oferta/akumulatory-samochodowe/", "oferta/akumulatory-samochodowe/do-aut-osobowych/")


def tech_text(p: dict) -> str:
    return (p["title"] + " " + " ".join(categories[c]["name"] for c in p["categories"] if c in categories)).lower()


def has_tech(p: dict, tech: str) -> bool:
    return re.search(rf"\b{tech}\b", tech_text(p)) is not None


def ah_value(p: dict) -> float | None:
    try:
        return float(str((p.get("filters") or {}).get("ah", "")).replace(",", "."))
    except ValueError:
        return None


def amps(p: dict) -> int | None:
    try:
        return int(float(str((p.get("filters") or {}).get("prad", "")).replace(",", ".")))
    except ValueError:
        return None


def group_of(p: dict) -> str:
    """Dział produktu do podziału strony zbiorczej: osobowe, ciężarowe, motocyklowe, żelowe..."""
    real = [c for c in p["categories"] if c in categories and categories[c]["name"].strip().lower() != "sklep"]
    deepest = max(real, key=lambda c: len(cat_chain(c)))
    segs = to_path(categories[deepest]["url"]).split("/")[1:]
    key = segs[1] if segs[0] == "akumulatory-samochodowe" and len(segs) > 2 and segs[1] else segs[0]
    return GROUP_SUFFIX.get(key, sentence(cat_chain(deepest)[0]["name"].strip()).lower())


def is_car_start_stop(p: dict) -> bool:
    return (has_tech(p, "agm") or has_tech(p, "efb")) and group_of(p) == "do aut osobowych"


def ah_text(n: int) -> list[tuple[str, str]]:
    return [(f"Jak dobrać akumulator {n} Ah",
             "<p>Sama pojemność nie wystarczy. Porównaj nowy akumulator z obecnym: prąd rozruchu (A, EN), biegunowość "
             "(prawy albo lewy plus), wymiary i mocowanie, a w aucie ze start-stop także technologię "
             f'(<a href="{PREFIX}oferta/akumulatory-efb/">EFB</a> albo <a href="{PREFIX}oferta/akumulatory-agm/">AGM</a>). '
             "Najprościej podać nam model auta albo przyjechać do sklepu: dobierzemy akumulator i zamontujemy go przy odbiorze.</p>")]


COLLECTIONS = [
    {"slug": "akumulatory-agm", "h1": "Akumulatory AGM", "title": "Akumulatory AGM", "label": "AGM", "match": lambda p: has_tech(p, "agm"),
     "text": [("Czym jest akumulator AGM",
               "<p>AGM (Absorbent Glass Mat) to akumulator, w którym elektrolit jest uwięziony w macie z włókna szklanego. "
               "Jest bezobsługowy i szczelny. W samochodach stosuje się go w autach z rozbudowanym systemem start-stop, "
               "zwłaszcza z odzyskiem energii hamowania, i w autach z bogatym wyposażeniem elektrycznym. "
               "W motocyklach AGM to popularna bezobsługowa wersja akumulatora.</p>"),
              ("Wymiana akumulatora AGM",
               "<p>AGM wymienia się tylko na AGM. Producenci akumulatorów, np. VARTA, odradzają montaż EFB w miejsce AGM, "
               "bo system zarządzania energią auta jest dobrany do tej technologii. Po wymianie w aucie ze start-stop nowy akumulator "
               f"trzeba zwykle dopisać do komputera auta: {KOD} jest bezpłatne przy zakupie akumulatora w naszym sklepie. "
               f"Robimy też {PODTRZ}, żeby nie stracić ustawień.</p>")]},
    {"slug": "akumulatory-efb", "h1": "Akumulatory EFB", "title": "Akumulatory EFB", "label": "EFB", "match": lambda p: has_tech(p, "efb"),
     "text": [("Czym jest akumulator EFB",
               "<p>EFB (Enhanced Flooded Battery) to ulepszony akumulator kwasowo-ołowiowy z płynnym elektrolitem, trwalszy "
               "przy częstych rozruchach niż zwykły. Jest przeznaczony do aut z prostszym systemem start-stop, zwykle bez odzysku "
               "energii hamowania, a także do aut, które jeżdżą głównie po mieście, i do aut z bogatszym wyposażeniem.</p>"),
              ("Wymiana akumulatora EFB",
               "<p>EFB można wymienić na EFB albo na AGM. AGM warto wybrać, gdy w aucie pracuje dużo odbiorników prądu albo "
               "akumulator często się rozładowuje. W drugą stronę to nie działa: AGM zawsze zastępuje się AGM. "
               f"Po wymianie w aucie ze start-stop wykonujemy {KOD}, przy zakupie u nas bezpłatnie.</p>")]},
    {"slug": "akumulatory-start-stop", "h1": "Akumulatory do aut ze start-stop", "title": "Akumulatory start-stop",
     "label": "do aut ze start-stop", "match": is_car_start_stop,
     "text": [("EFB czy AGM do auta ze start-stop",
               "<p>Decyduje to, jaki akumulator zamontował producent auta. AGM stosuje się w autach z rozbudowanym systemem "
               "start-stop i odzyskiem energii hamowania, EFB w prostszych systemach. AGM wymienia się tylko na AGM, a EFB "
               "na EFB albo AGM. Jeśli nie wiesz, jaki akumulator masz w aucie, podaj nam model albo przyjedź: sprawdzimy i dobierzemy.</p>"),
              ("Wymiana akumulatora w aucie ze start-stop",
               "<p>Akumulator start-stop współpracuje z czujnikiem i systemem zarządzania energią auta. Po wymianie nowy akumulator "
               f"trzeba dopisać do komputera auta ({KOD}, przy zakupie u nas bezpłatne). Przez kilka godzin po wymianie start-stop "
               f"może jeszcze nie działać, zanim auto rozpozna nowy akumulator. Robimy też {PODTRZ}.</p>")]},
    *({"slug": f"akumulatory-{n}ah", "h1": f"Akumulatory {n} Ah", "title": f"Akumulatory {n}Ah", "label": f"{n} Ah",
       "match": (lambda n: lambda p: ah_value(p) == n)(n), "text": ah_text(n)} for n in (60, 74, 100)),
]


def collection_items() -> dict[str, list[dict]]:
    pool = [p for p in products.values() if p["id"] in product_pages and product_kind(p) == "battery"]
    return {c["slug"]: sorted((p for p in pool if c["match"](p)),
                              key=lambda p: (ah_value(p) or 0, amps(p) or 0, p["title"], p["id"])) for c in COLLECTIONS}


def collection_links(items: dict[str, list[dict]], skip: str = "") -> str:
    return " · ".join(f'<a href="{PREFIX}oferta/{c["slug"]}/">{esc(c["label"])}</a> ({len(items[c["slug"]])})'
                      for c in COLLECTIONS if c["slug"] != skip and items[c["slug"]])


def collection_nav(items: dict[str, list[dict]]) -> str:
    tech = [c for c in COLLECTIONS if not c["slug"].endswith("ah")]
    cap = [c for c in COLLECTIONS if c["slug"].endswith("ah")]
    link = lambda c: f'<a href="{PREFIX}oferta/{c["slug"]}/">{esc(c["label"])}</a> ({len(items[c["slug"]])})'  # noqa: E731
    return ('<div class="service-copy brand-copy collection-nav" data-collections=""><div class="prose"><p>'
            f'Według technologii: {" · ".join(link(c) for c in tech)}. Popularne pojemności: {" · ".join(link(c) for c in cap)}.'
            '</p></div></div>')


def collection_filter(items: dict[str, list[dict]]) -> str:
    """Grupa linków w panelu filtrów katalogu (bez pól formularza, więc nie wpływa na filtrowanie w catalog.js)."""
    rows = "".join(f'<li><a href="{PREFIX}oferta/{c["slug"]}/">{esc(c["label"][0].upper() + c["label"][1:])}<small>{len(items[c["slug"]])}</small></a></li>'
                   for c in COLLECTIONS if items[c["slug"]])
    return ('<details class="filter-group" data-collections-filter="" open=""><summary>Technologia i pojemność'
            f'<span aria-hidden="true">+</span></summary><ul class="category-tree">{rows}</ul></details>')


def build_collection_pages(items: dict[str, list[dict]]) -> dict[str, dict]:
    head_part, tail = shell(SITE / "marki" / "index.html")
    meta = {}
    for c in COLLECTIONS:
        its = items[c["slug"]]
        if not its:
            continue
        h1 = c["h1"]
        groups = collections.Counter(group_of(p) for p in its)
        # auta osobowe zawsze pierwsze: tak szuka większość (np. "akumulator agm" to głównie auta ze start-stop)
        order = sorted(groups, key=lambda g: (g != "do aut osobowych", -groups[g], g))
        bcount = collections.Counter(p["brand"] for p in its if p.get("brandId") in brands)
        brand_ids = {p["brand"]: p["brandId"] for p in its if p.get("brandId") in brands}
        blinks = ", ".join(f'<a href="{PREFIX}marki/{brand_slug[brand_ids[b]]}/">{esc(b)}</a>' for b, _ in bcount.most_common())
        split = (" – " + ", ".join(f"{g} ({groups[g]})" for g in order)) if len(order) > 1 else ""
        spec = ""
        if c["slug"].endswith("ah"):
            # bez liczenia biegunów: część produktów nie ma bieguna w danych, a w trzech dane są sprzeczne (README)
            a = [amps(p) for p in its if amps(p)]
            if a:
                spec = f" Prąd rozruchu od {min(a)} do {max(a)} A."
        intro = (f"<p>{esc(h1)} w naszej ofercie: {plural(len(its))}{split}. Marki: {blinks}.{spec} "
                 f'Zapytaj o dostępność w sklepach w Tarnowie i Radłowie albo zadzwoń: <a href="tel:{PHONE}">{PHONE_DISPLAY}</a>. '
                 "Przy odbiorze akumulatora w sklepie stacjonarnym montaż jest bezpłatny.</p>")
        body = "".join(f"<h2>{esc(h)}</h2>{t}" for h, t in c["text"])
        see = f'<p>Zobacz też: {collection_links(items, c["slug"])} · <a href="{PREFIX}oferta/">wszystkie akumulatory</a></p>'
        if len(order) > 1:
            grids = "".join(f'<section class="collection-group"><h2>{esc(h1)} {esc(g)}<span>{plural(groups[g])}</span></h2>'
                            '<div class="product-grid">' + "".join(card(p) for p in its if group_of(p) == g) + "</div></section>"
                            for g in order)
        else:
            grids = '<div class="product-grid">' + "".join(card(p) for p in its) + "</div>"
        main = (f'<main id="main"><div class="page-top visual-page-top" style=\'--page-photo:url("{PHOTO}")\'>'
                + crumbs_html([("Strona główna", PREFIX), ("Akumulatory", f"{PREFIX}oferta/"), (h1, "")])
                + f'<h1>{esc(h1)}</h1></div>'
                + '<div class="service-copy brand-copy"><div class="prose">' + intro + body + see + "</div></div>"
                + f'<div class="catalog-results brand-results collection-results"><div class="results-toolbar"><p>{plural(len(its))}</p></div>'
                + grids + "</div></main>")
        top = ", ".join(b for b, _ in bcount.most_common(3))
        desc = fit_desc(*(f"{h1}: {plural(len(its))}" + (f" ({top})" if top else "") + "." + t for t in (
            f" Bezpłatny montaż przy odbiorze w sklepie – Tarnów (Krakowska 150, Giełdowa 5) i Radłów. Tel. {PHONE_DISPLAY}.",
            f" Bezpłatny montaż przy odbiorze w sklepie w Tarnowie i Radłowie. Tel. {PHONE_DISPLAY}.",
            " Bezpłatny montaż przy odbiorze w sklepie w Tarnowie i Radłowie.")))
        page = head_part + main + tail
        page = set_title(page, f'{c["title"]} Tarnów | {BRAND}')
        page = set_description(page, desc)
        path = f'oferta/{c["slug"]}/'
        write(SITE / path / "index.html", page)
        meta[path] = {"name": h1, "description": desc, "items": [to_path(p["url"]) for p in its]}
    return meta


def product_collections_html(p: dict, items: dict[str, list[dict]]) -> str:
    own = [c for c in COLLECTIONS if any(x["id"] == p["id"] for x in items[c["slug"]])]
    if not own:
        return ""
    return ('<p class="product-collections" data-collections="">Zobacz też: '
            + " · ".join(f'<a href="{PREFIX}oferta/{c["slug"]}/">{esc(c["h1"])}</a>' for c in own) + "</p>")


def build_location_pages() -> None:
    head_part, tail = shell(SITE / "nasze-sklepy" / "index.html")
    for loc in LOCATIONS:
        others = "".join(f'<li><a href="{PREFIX}nasze-sklepy/{o["slug"]}/">{esc(o["label"])}</a></li>' for o in LOCATIONS if o is not loc)
        gbp = (f'<a class="text-link" href="{esc(loc["gbp"])}" rel="noopener" target="_blank">Opinie i wizytówka w Google ↗</a>' if loc["gbp"] else "")
        main = (f'<main id="main"><div class="page-top visual-page-top" style=\'--page-photo:url("{PHOTO}")\'>'
                + crumbs_html([("Strona główna", PREFIX), ("Nasze sklepy", f"{PREFIX}nasze-sklepy/"), (loc["label"], "")])
                + f'<h1>Sklep z akumulatorami – {esc(loc["label"])}</h1></div>'
                + '<div class="location-grid"><article class="location-card">'
                + f'<h2>{esc(loc["street"])}</h2><p>{esc(loc["city"])}, {esc(loc["zip"])}</p>'
                + f'<a class="location-phone" href="tel:{loc["phone"]}">tel: (+48) {loc["phone_display"]}</a>'
                + hours_html(loc)
                + f'<a class="text-link" href="{esc(loc["map"])}" rel="noopener" target="_blank">Pokaż na mapie i wyznacz trasę ↗</a>'
                + gbp + "</article></div>"
                + '<div class="information-copy"><div class="prose">'
                + f'<p>Sklep Pogotowia Akumulatorowego przy {esc(loc["street"])} w miejscowości {esc(loc["city"])}. '
                  f'Zadzwoń pod <a href="tel:{loc["phone"]}">{loc["phone_display"]}</a>, żeby sprawdzić dostępność akumulatora do Twojego pojazdu.</p>'
                + "<h2>Gratis przy zakupie i w sklepie</h2><ul>" + "".join(f"<li>{esc(s)}</li>" for s in FREE_SERVICES) + "</ul>"
                + f'<h2>Oferta i usługi</h2><p><a href="{PREFIX}oferta/">Akumulatory i prostowniki</a> · <a href="{PREFIX}uslugi/">Nasze usługi</a> · '
                  f'<a href="{PREFIX}uslugi/odpalenie-unieruchomionego-pojazdu/">Pogotowie akumulatorowe</a></p>'
                + f"<h2>Pozostałe sklepy</h2><ul>{others}</ul></div></div></main>")
        page = head_part + main + tail
        page = set_title(page, fit_title(f"Akumulatory {loc['city']}, {loc['street']} – sklep"))
        page = set_description(page, f"Sklep z akumulatorami: {loc['street']}, {loc['zip']} {loc['city']}. Tel. {loc['phone_display']}. "
                                     f"Bezpłatny test akumulatora z wydrukiem i montaż przy odbiorze w sklepie.")
        write(SITE / "nasze-sklepy" / loc["slug"] / "index.html", page)


# ---------------------------------------------------------------- JSON-LD
ORG_ID = f"{PROD_ORIGIN}/#organization"
SITE_ID = f"{PROD_ORIGIN}/#website"


def loc_id(loc: dict) -> str:
    return f"{PROD_ORIGIN}/nasze-sklepy/{loc['slug']}/#store"


def org() -> dict:
    return {"@type": "Organization", "@id": ORG_ID, "name": BRAND, "url": f"{PROD_ORIGIN}/",
            "logo": f"{PROD_ORIGIN}/assets/media/logo-schema.png", "telephone": PHONE, "email": EMAIL,
            "sameAs": [FACEBOOK, LOCATIONS[0]["gbp"]],
            "department": [{"@id": loc_id(l)} for l in LOCATIONS]}


def store(loc: dict) -> dict:
    d = {"@type": "AutoPartsStore", "@id": loc_id(loc), "name": f"{BRAND} – {loc['label']}",
         "url": f"{PROD_ORIGIN}/nasze-sklepy/{loc['slug']}/", "telephone": loc["phone"], "email": EMAIL,
         "image": f"{PROD_ORIGIN}/assets/media/og-default.jpg",
         "address": {"@type": "PostalAddress", "streetAddress": loc["street"], "postalCode": loc["zip"],
                     "addressLocality": loc["city"], "addressRegion": "małopolskie", "addressCountry": "PL"},
         "parentOrganization": {"@id": ORG_ID}, "hasMap": loc["gbp"] or loc["map"],
         "areaServed": {"@type": "City", "name": "Tarnów"}}
    if loc.get("geo"):
        d["geo"] = {"@type": "GeoCoordinates", "latitude": loc["geo"][0], "longitude": loc["geo"][1]}
    if loc.get("hours"):
        d["openingHoursSpecification"] = [
            {"@type": "OpeningHoursSpecification", "dayOfWeek": h["days"], "opens": h["opens"], "closes": h["closes"]}
            for h in loc["hours"] if h["opens"]]
    return d


def hours_html(loc: dict) -> str:
    """Lista godzin otwarcia sklepu; pusta, gdy brak danych."""
    if not loc.get("hours"):
        return ""
    fmt = lambda t: t.lstrip("0") if t[0] == "0" else t  # noqa: E731
    rows = "".join(f'<li>{esc(h["label"])}: {fmt(h["opens"])}–{fmt(h["closes"])}</li>' if h["opens"]
                   else f'<li>{esc(h["label"])}: nieczynne</li>' for h in loc["hours"])
    return f'<h3>Godziny otwarcia</h3><ul class="opening-hours">{rows}</ul>'


def directions_link(url: str) -> str:
    """Linki map wyszukujące adres zamienia na trasę do właściwej wizytówki (pod 'Giełdowa 5' Google pokazuje też Agadar)."""
    def sub(m: re.Match) -> str:
        q = unquote(html.unescape(m.group(1)))
        for loc in LOCATIONS:
            if loc["street"].replace("ul. ", "") in q:
                return html.escape(loc["map"], quote=True)
        return m.group(0)
    return re.sub(r"https://www\.google\.com/maps/search/\?api=1&amp;query=([^\"]+)", sub, url)


def breadcrumb_ld(items: list[tuple[str, str]]) -> dict | None:
    if len(items) < 2:
        return None
    out = []
    for i, (name, href) in enumerate(items, 1):
        el = {"@type": "ListItem", "position": i, "name": name}
        if href:
            el["item"] = prod_url(to_path(href))
        out.append(el)
    return {"@type": "BreadcrumbList", "itemListElement": out}


def head_block(path: str, text: str, og_type: str, image: str, graph: list[dict], robots: str | None = None) -> str:
    title, desc = get_title(text), get_desc(text)
    url = prod_url(path)
    tags = [f'<link href="{url}" rel="canonical"/>']
    if robots:
        tags.append(f'<meta content="{robots}" name="robots"/>')
    tags += [f'<meta content="{og_type}" property="og:type"/>', f'<meta content="{esc(title)}" property="og:title"/>',
             f'<meta content="{esc(desc)}" property="og:description"/>', f'<meta content="{url}" property="og:url"/>',
             f'<meta content="{image}" property="og:image"/>', '<meta content="pl_PL" property="og:locale"/>',
             f'<meta content="{BRAND}" property="og:site_name"/>', '<meta content="summary_large_image" name="twitter:card"/>']
    if graph:
        ld = json.dumps({"@context": "https://schema.org", "@graph": graph}, ensure_ascii=False, separators=(",", ":"))
        ld = ld.replace("</", "<\\/")
        tags.append(f'<script type="application/ld+json">{ld}</script>')
    return SEO_START + "".join(tags) + SEO_END


def inject_head(text: str, block: str) -> str:
    text = re.sub(re.escape(SEO_START) + ".*?" + re.escape(SEO_END), "", text, flags=re.S)
    return text.replace("</head>", block + "</head>", 1)


OG_DEFAULT = f"{PROD_ORIGIN}/assets/media/og-default.jpg"


# ---------------------------------------------------------------- service content
def service_extra(slug: str) -> str:
    s = SERVICES[slug]
    parts = ['<section class="service-more prose" data-seo-extra="">']
    for heading, kind, items in s["sections"]:
        parts.append(f"<h2>{esc(heading)}</h2><{kind}>" + "".join(f"<li>{esc(i)}</li>" for i in items) + f"</{kind}>")
    parts.append("<h2>Gratis w naszych sklepach</h2><ul>" + "".join(f"<li>{esc(i)}</li>" for i in FREE_SERVICES) + "</ul>")
    if s["faq"]:
        parts.append("<h2>Najczęstsze pytania</h2>")
        for q, a in s["faq"]:
            parts.append(f"<h3>{esc(q)}</h3><p>{esc(a)}</p>")
    parts.append(f'<p>Pomoc na terenie Tarnowa: <a href="tel:{PHONE}">{PHONE_DISPLAY}</a> · '
                 f'<a href="{PREFIX}nasze-sklepy/">nasze sklepy</a></p></section>')
    return "".join(parts)


# ---------------------------------------------------------------- images and performance
MEDIA = SITE / "assets" / "media"
LOGO_PNG = MEDIA / "logo-akumulatory-tarnow.png"


def optimize_images() -> None:
    from PIL import Image
    logo = Image.open(LOGO_PNG).convert("RGBA")
    for w in (400, 1200):
        out = MEDIA / f"logo-akumulatory-tarnow-{w}.webp"
        if not out.exists():
            logo.resize((w, round(logo.height * w / logo.width)), Image.LANCZOS).save(out, "WEBP", quality=88, method=6)
    bg = (24, 29, 24, 255)  # #181d18, kolor motywu strony
    if not (MEDIA / "logo-schema.png").exists():
        sq = Image.new("RGBA", (600, 600), bg)
        lw = 520
        lg = logo.resize((lw, round(logo.height * lw / logo.width)), Image.LANCZOS)
        sq.alpha_composite(lg, ((600 - lg.width) // 2, (600 - lg.height) // 2))
        sq.convert("RGB").save(MEDIA / "logo-schema.png", optimize=True)
    if not (MEDIA / "og-default.jpg").exists():
        og = Image.new("RGBA", (1200, 630), bg)
        lw = 900
        lg = logo.resize((lw, round(logo.height * lw / logo.width)), Image.LANCZOS)
        og.alpha_composite(lg, ((1200 - lg.width) // 2, (630 - lg.height) // 2))
        og.convert("RGB").save(MEDIA / "og-default.jpg", quality=85, optimize=True)


def patch(path: Path, pairs: list[tuple[str, str]]) -> None:
    text = read(path)
    new = text
    for old, rep in pairs:
        if rep not in new:
            new = new.replace(old, rep)
    if new != text:
        write(path, new)


MOBILE_HERO_EARLY = ("<script>(function(){if(!matchMedia('(max-width:991px), (hover:none) and (pointer:coarse)').matches)return;"
                     "var t=document.querySelector('.film-story');if(!t)return;var q=function(s){return t.querySelector(s)};"
                     "var h=q('.mobile-film-heading'),sv=q('.mobile-film-services'),hp=q('.mobile-help'),e=q('.film-eyebrow'),ti=q('.film-headline'),"
                     "o=q('.film-left'),a=q('.film-right'),st=q('.hero-running-copy');if(!h||!sv||!hp||!e||!ti||!o||!a||!st)return;"
                     "var m=window.__mobileHeroOriginal=new Map();[e,ti,o,a,st].forEach(function(x){m.set(x,{element:x,parent:x.parentNode,next:x.nextSibling})});"
                     "h.append(e,ti);hp.prepend(a);sv.append(o);t.append(st);t.classList.add('is-mobile-hero')})();</script>")
MOBILE_BATTERY_EARLY = ("<script>(function(){if(!matchMedia('(max-width:991px), (hover:none) and (pointer:coarse)').matches)return;"
                        "var b=document.querySelector('.mobile-battery-offer'),tb=document.querySelector('.services-overview .mobile-trusted-brands');"
                        "if(!b||!tb)return;var m=window.__mobileHeroOriginal||(window.__mobileHeroOriginal=new Map());"
                        "m.set(b,{element:b,parent:b.parentNode,next:b.nextSibling});tb.before(b)})();</script>")


def section_end(text: str, start: int) -> int:
    depth = 0
    for m in re.finditer(r"<section\b|</section>", text[start:]):
        depth += 1 if m.group().startswith("<section") else -1
        if depth == 0:
            return start + m.end()
    return -1


def patch_assets() -> None:
    a = SITE / "assets"
    patch(a / "catalog.css", [("assets/media/logo-akumulatory-tarnow.png'", "assets/media/logo-akumulatory-tarnow-400.webp'")])
    patch(a / "mobile.css", [("assets/media/logo-akumulatory-tarnow.png'", "assets/media/logo-akumulatory-tarnow-400.webp'")])
    # strony zbiorcze: nagłówki grup produktów i linki "Zobacz też" na stronach produktów
    css = read(a / "catalog.css")
    if "/* seo: strony zbiorcze */" not in css:
        write(a / "catalog.css", css.rstrip("\n") + "\n/* seo: strony zbiorcze */\n"
              ".collection-group+.collection-group{margin-top:48px}"
              ".collection-group>h2{display:flex;align-items:baseline;gap:12px;flex-wrap:wrap;font-size:22px;line-height:1.3;letter-spacing:-.02em;margin:0 0 18px}"
              ".collection-group>h2 span{color:var(--muted);font-size:13px;font-weight:400;letter-spacing:0}"
              ".collection-nav{margin-bottom:40px}"
              ".product-collections{margin-top:18px;font-size:13px;line-height:1.6;color:var(--muted)}"
              ".product-collections a{color:var(--ink);text-decoration:underline;text-underline-offset:3px}\n")
    # CLS desktop: hero przechodzi na position:absolute; wyśrodkowanie przez inset:0 + margin:auto zamiast
    # left/top:50% + translate, żeby pozycja layoutu (liczona przez CLS bez transformacji) się nie zmieniała.
    vh = read(a / "video-hero.css").replace("\n.enhanced-motion .film-story>.energy-camera{height:100svh}", "")
    anchor = ".enhanced-motion .film-story.is-scrubbing>.film-continuation-range{display:block;height:240svh}"
    rule = ".enhanced-motion .film-story .film-hero{left:0;top:0;right:0;bottom:0;margin:auto;translate:none}"
    if rule not in vh:
        vh = vh.replace(anchor, anchor + "\n" + rule, 1)
    write(a / "video-hero.css", vh)
    # mobile-hero.js: użyj pozycji zapamiętanych przez wczesny skrypt inline (zmiana układu przed pierwszym renderem)
    patch(a / "mobile-hero.js", [("const originalPositions = [eyebrow, title, offer, assistance, statement, batteries].map(element => ({",
                                  "const early = window.__mobileHeroOriginal;\n  const originalPositions = [eyebrow, title, offer, assistance, statement, batteries].map(element => early?.get(element) || ({")])
    # lightbox: obraz tworzony przy otwarciu zamiast <img> bez src w HTML
    patch(a / "catalog.js", [("const large = one('[data-large-image]',popup);",
                              "let large = one('[data-large-image]',popup);\n    if (!large) { large = document.createElement('img'); large.setAttribute('data-large-image',''); const slot = one('[data-large-image-slot]',popup); slot ? slot.replaceWith(large) : popup.append(large); }")])
    idx = SITE / "index.html"
    text = read(idx)
    text = text.replace('<img src="assets/media/logo-akumulatory-tarnow.png" width="2172" height="724" alt=""/>',
                        '<img src="assets/media/logo-akumulatory-tarnow-400.webp" width="400" height="133" alt=""/>')
    text = text.replace('<img src="assets/media/logo-akumulatory-tarnow.png" width="2172" height="724" alt="" decoding="async"/>',
                        '<img src="assets/media/logo-akumulatory-tarnow-1200.webp" width="1200" height="400" alt="" decoding="async"/>')
    pre400 = '<link as="font" crossorigin="" href="assets/fonts/oswald-400.woff2" rel="preload" type="font/woff2"/>'
    if pre400 not in text:
        text = text.replace('<link as="font" crossorigin="" href="assets/fonts/oswald-700.woff2" rel="preload" type="font/woff2"/>',
                            '<link as="font" crossorigin="" href="assets/fonts/oswald-700.woff2" rel="preload" type="font/woff2"/>' + pre400, 1)
    if "__mobileHeroOriginal=new Map()" not in text:
        hero_start = text.rfind("<section", 0, text.index('class="film-story'))
        end = section_end(text, hero_start)
        text = text[:end] + MOBILE_HERO_EARLY + text[end:]
    if "tb.before(b)" not in text:
        tb = text.index('<section class="mobile-trusted-brands"')
        end = section_end(text, tb)
        text = text[:end] + MOBILE_BATTERY_EARLY + text[end:]
    write(idx, text)


def build_404() -> None:
    head_part, tail = shell(SITE / "nasze-sklepy" / "index.html")
    main = (f'<main id="main"><div class="page-top visual-page-top" style=\'--page-photo:url("{PHOTO}")\'>'
            + crumbs_html([("Strona główna", PREFIX), ("Nie znaleziono strony", "")])
            + '<h1>Nie znaleziono strony</h1><div class="prose"><p>Tej strony nie ma albo zmieniła adres. Sprawdź ofertę albo zadzwoń: '
              f'<a href="tel:{PHONE}">{PHONE_DISPLAY}</a>.</p></div></div><div class="subcategory-links">'
            + "".join(f'<a href="{PREFIX}{p}">{n}<span aria-hidden="true">↗</span></a>' for p, n in
                      (("oferta/", "Akumulatory"), ("marki/", "Marki"), ("uslugi/", "Usługi"), ("nasze-sklepy/", "Nasze sklepy"), ("kontakt/", "Kontakt")))
            + "</div></main>")
    page = head_part + main + tail
    page = set_title(page, f"Nie znaleziono strony | {BRAND}")
    page = set_description(page, "Ta strona nie istnieje. Zobacz ofertę akumulatorów albo skontaktuj się z nami.")
    page = page.replace("</head>", '<meta content="noindex" name="robots"/></head>', 1) if 'name="robots"' not in page else page
    write(SITE / "404.html", page)


def write_redirects() -> None:
    """Reguły 301 dla serwera (Apache/LiteSpeed .htaccess oraz Netlify/Cloudflare _redirects) z istniejących stron-przekierowań."""
    rules = []
    for page in sorted(SITE.rglob("*.html")):
        t = read(page)
        if not is_stub(t):
            continue
        m = re.search(r'content="0;url=([^"]+)"', t)
        if not m:
            continue
        target = "/" + to_path(html.unescape(m.group(1)))
        if target.lstrip("/") in DEMO_BLOG:
            target = "/porady/"
        r = page.relative_to(SITE).as_posix()
        old = "/" + (r[: -len("/index.html")] if r.endswith("/index.html") else r)
        if old.strip("/") in ("4-men", "5-women", "7-stationery", "8-home-accessories"):
            continue
        rules.append((old, target))
    lines = ["# Wygenerowane przez tools/seo/apply_seo.py: przekierowania 301 ze starego sklepu PrestaShop.",
             "# Trzymać co najmniej 12 miesięcy (Google: site moves with URL changes).", "",
             "ErrorDocument 404 /404.html", "Options -Indexes", "",
             "<IfModule mod_headers.c>",
             '  Header always set X-Content-Type-Options "nosniff"',
             '  Header always set Referrer-Policy "strict-origin-when-cross-origin"',
             '  Header always set X-Frame-Options "SAMEORIGIN"',
             '  Header always set Strict-Transport-Security "max-age=31536000"',
             '  <FilesMatch "\\.(webp|avif|jpg|jpeg|png|svg|woff2|mp4)$">', '    Header set Cache-Control "public, max-age=31536000, immutable"', "  </FilesMatch>",
             '  <FilesMatch "\\.(css|js|json)$">', '    Header set Cache-Control "public, max-age=604800"', "  </FilesMatch>",
             "</IfModule>", "",
             "<IfModule mod_rewrite.c>", "  RewriteEngine On",
             "  RewriteCond %{HTTPS} off [OR]", "  RewriteCond %{HTTP_HOST} !^www\\. [NC]",
             "  RewriteRule ^ https://www.akumulatory-tarnow.pl%{REQUEST_URI} [R=301,L]",
             "  RewriteRule ^logowanie/?$ / [R=301,L]",
             "  RewriteRule ^(4-men|5-women|7-stationery|8-home-accessories)/?$ - [G,L]",
             "</IfModule>", "", "<IfModule mod_alias.c>"]
    for old, target in rules:
        lines.append(f"  RedirectMatch 301 ^{re.escape(old)}/?$ {target}")
    lines.append("</IfModule>")
    write(SITE / ".htaccess", "\n".join(lines) + "\n")
    write(SITE / "_redirects", "# Netlify / Cloudflare Pages: przekierowania 301 ze starego sklepu\n/logowanie / 301\n"
          + "".join(f"{old} {target} 301\n" for old, target in rules))


# ---------------------------------------------------------------- main pass
def main() -> None:
    optimize_images()
    patch_assets()
    brand_meta = build_brand_pages()
    coll_items = collection_items()
    coll_meta = build_collection_pages(coll_items)
    build_location_pages()
    build_404()
    href_brand = {bid: f"{PREFIX}marki/{brand_slug[bid]}/" for bid in brands}
    sitemap: list[str] = []
    dup_h1_fixed = 0
    for page in sorted(SITE.rglob("*.html")):
        text = read(page)
        if is_stub(text):
            # stare adresy marek: kieruj od razu na strony marek (albo na /marki/, gdy marka nie ma produktów)
            new = re.sub(r"/akumulatory-tarnow-v2/oferta/\?marka=(\d+)", lambda m: href_brand.get(int(m.group(1)), f"{PREFIX}marki/")
                         if int(m.group(1)) in brands and (SITE / to_path(href_brand[int(m.group(1))]) / "index.html").exists() else f"{PREFIX}marki/", text)
            for demo in DEMO_BLOG:
                new = new.replace(f"{PREFIX}{demo}", f"{PREFIX}porady/")
            if new != text:
                write(page, new)
            continue
        if page.name == "404.html":
            continue
        path = rel(page)
        orig = text
        graph: list[dict] = []
        og_type, image, robots = "website", OG_DEFAULT, None
        crumbs = breadcrumbs(text)

        # globalne poprawki treści
        text = text.replace("Pogotowie Akumlatorowe", "Pogotowie Akumulatorowe")
        text = directions_link(text)
        text = text.replace("w TARNOWE ", "w TARNOWIE ").replace(" trzymujesz", " otrzymujesz").replace("profesjonale ", "profesjonalne ")
        # pomija świadomy link "Filtruj w katalogu" ze stron marek (data-filter-link)
        text = re.sub(r'(?<!data-filter-link="" )href="/akumulatory-tarnow-v2/oferta/\?marka=(\d+)"', lambda m: f'href="{href_brand.get(int(m.group(1)), PREFIX + "marki/")}"', text)
        text = re.sub(r'"href": "/akumulatory-tarnow-v2/oferta/\?marka=(\d+)"', lambda m: f'"href": "{href_brand.get(int(m.group(1)), PREFIX + "marki/")}"', text)
        text = text.replace('<img alt="" data-large-image=""/>', '<span data-large-image-slot=""></span>')
        # linki do stron zbiorczych (AGM, EFB, start-stop, pojemności) na stronie oferty i w działach samochodowych
        text = re.sub(r'<div class="service-copy brand-copy collection-nav" data-collections="">.*?</p></div></div>', "", text, flags=re.S)
        if path in COLL_NAV_PAGES:
            anchor = '<div class="subcategory-links">' if '<div class="subcategory-links">' in text else '<div class="catalog-layout">'
            text = text.replace(anchor, collection_nav(coll_items) + anchor, 1)
        # te same linki na górze panelu filtrów każdej strony katalogu, nad rozwiniętym drzewem "Kategorie"
        # (na telefonie panel trafia do okna "Filtry")
        text = re.sub(r'<details class="filter-group" data-collections-filter="" open="">.*?</details>', "", text, flags=re.S)
        form_at = text.find('id="catalog-filter-form"')
        if form_at > 0:
            slots = [i for i in (text.find('<details class="filter-group"', form_at), text.find('<fieldset class="filter-group"', form_at)) if i > 0]
            if slots:
                text = text[:min(slots)] + collection_filter(coll_items) + text[min(slots):]

        if path in PAGES:
            text = set_title(text, PAGES[path]["title"])
            text = set_description(text, PAGES[path]["description"])

        if path == "":
            graph = [org(), {"@type": "WebSite", "@id": SITE_ID, "name": BRAND, "url": f"{PROD_ORIGIN}/", "inLanguage": "pl-PL", "publisher": {"@id": ORG_ID}}]
            graph += [store(l) for l in LOCATIONS]
        elif path in ("kontakt/", "nasze-sklepy/"):
            graph = [org()] + [store(l) for l in LOCATIONS]
            # karty sklepów linkują do stron lokalizacji
            for loc in LOCATIONS:
                text = text.replace(f'<h2>{loc["street"]}</h2>', f'<h2><a href="{PREFIX}nasze-sklepy/{loc["slug"]}/">{loc["street"]}</a></h2>', 1)
        elif path.startswith("nasze-sklepy/") and path.count("/") == 2:
            loc = next(l for l in LOCATIONS if path == f"nasze-sklepy/{l['slug']}/")
            graph = [store(loc)]
        elif path.startswith("produkty/"):
            pid = int(re.match(r"produkty/(\d+)-", path).group(1))
            p = products.get(pid, {})
            f = p.get("filters") or {}
            pol = polarity(p)
            base_title = p.get("title") or get_title(text).split(" | ")[0]
            dup = title_count[base_title.strip().lower()] > 1
            extra = disambiguator(p) if dup and p else ""
            shown = f"{base_title} ({extra})" if extra else base_title
            if extra:
                text = set_h1(text, shown)
                dup_h1_fixed += 1
            text = set_title(text, fit_title(shown))
            ref = p.get("reference") or ""
            kind = product_kind(p) if p else "battery"
            bits = [f"{f['ah']} Ah" if f.get("ah") else "", f"{f['prad']} A" if f.get("prad") else "", f"biegun {pol}" if pol else "", f"indeks {ref}" if ref else ""]
            spec = ", ".join(b for b in bits if b)
            tails = ([" Bezpłatny montaż przy odbiorze w sklepie w Tarnowie. Tel. 500 399 154.",
                      " Bezpłatny montaż przy odbiorze w sklepie w Tarnowie.", " Bezpłatny montaż przy odbiorze w sklepie."]
                     if kind == "battery" else
                     [" Zapytaj o dostępność w sklepach w Tarnowie i Radłowie: 500 399 154.", " Sklepy w Tarnowie i Radłowie: 500 399 154."])
            # biegun i indeks są już w specyfikacji, więc w opisie wystarczy nazwa bez dopisku
            lead = base_title + (f": {spec}." if spec else ".")
            text = set_description(text, fit_desc(*(lead + t for t in tails)))
            img = re.search(r'<figure class="product-media">.*?src="([^"]+)"', text, flags=re.S)
            image = prod_url(to_path(img.group(1))) if img else OG_DEFAULT
            og_type = "product"
            props = []
            for name, key in (("Pojemność (Ah)", "ah"), ("Prąd rozruchu (En)", "prad"), ("Polaryzacja", "biegun")):
                if f.get(key):
                    props.append({"@type": "PropertyValue", "name": name, "value": f[key]})
            dims = re.search(r"<dt>Wymiary \(dł/szer/wys\)</dt><dd>([^<]+)</dd>", text)
            if dims:
                props.append({"@type": "PropertyValue", "name": "Wymiary (dł/szer/wys)", "value": dims.group(1)})
            prod = {"@type": "Product", "name": shown, "image": image, "description": get_desc(text), "url": prod_url(path)}
            if ref:
                prod["sku"] = ref
            if p.get("brand"):
                prod["brand"] = {"@type": "Brand", "name": p["brand"]}
            if props:
                prod["additionalProperty"] = props
            graph = [prod]
            text = re.sub(r'<p class="product-collections" data-collections="">.*?</p>', "", text, flags=re.S)
            see = product_collections_html(p, coll_items) if p else ""
            if see:
                text = re.sub(r'(<dl class="product-parameters">.*?</dl>)', lambda m: m.group(1) + see, text, count=1, flags=re.S)
        elif path in coll_meta:
            m = coll_meta[path]
            graph = [{"@type": "CollectionPage", "name": m["name"], "description": m["description"], "url": prod_url(path),
                      "inLanguage": "pl-PL", "isPartOf": {"@id": SITE_ID},
                      "mainEntity": {"@type": "ItemList", "numberOfItems": len(m["items"]),
                                     "itemListElement": [{"@type": "ListItem", "position": i, "url": prod_url(u)} for i, u in enumerate(m["items"], 1)]}}]
        elif path.startswith("oferta/") and path != "oferta/":
            c = cat_by_path.get(path)
            if c:
                t = cat_title(c["id"])
                dup = name_count[c["name"].strip().lower()] > 1
                if dup:
                    text = set_h1(text, t)
                    dup_h1_fixed += 1
                text = set_title(text, fit_title(t))
                lead = f"{t}: {plural(c['count'])} w ofercie."
                battery = "akumulator" in cat_chain(c["id"])[0]["name"].lower()
                tails = ([f" Bezpłatny montaż akumulatora przy odbiorze w sklepie – Tarnów (Krakowska 150, Giełdowa 5) i Radłów. Tel. {PHONE_DISPLAY}.",
                          f" Bezpłatny montaż przy odbiorze w sklepie w Tarnowie i Radłowie. Tel. {PHONE_DISPLAY}.",
                          " Bezpłatny montaż przy odbiorze w sklepie w Tarnowie i Radłowie.", " Bezpłatny montaż przy odbiorze w sklepie."]
                         if battery else
                         [f" Sklepy w Tarnowie (Krakowska 150, Giełdowa 5) i Radłowie. Tel. {PHONE_DISPLAY}.",
                          f" Sklepy w Tarnowie i Radłowie. Tel. {PHONE_DISPLAY}.", " Sklepy w Tarnowie i Radłowie."])
                text = set_description(text, fit_desc(*(lead + x for x in tails)))
        elif path.startswith("marki/") and path in brand_meta:
            graph = [{"@type": "Brand", "name": brand_meta[path]["name"], "url": prod_url(path)}]
        elif path.startswith("uslugi/") and path != "uslugi/":
            slug = path.split("/")[1]
            if slug in SERVICES:
                s = SERVICES[slug]
                text = set_title(text, s["title"])
                text = set_description(text, s["description"])
                if s["h1"]:
                    text = set_h1(text, s["h1"])
                extra = service_extra(slug)
                text = re.sub(r'<section class="service-more prose" data-seo-extra="">.*?</section>', "", text, flags=re.S)
                text = text.replace('</div><a class="button-dark" href="tel:+48500399154">', '</div>' + extra + '<a class="button-dark" href="tel:+48500399154">', 1)
                graph = [{"@type": "Service", "name": s["h1"] or get_title(text).split(" – ")[0], "serviceType": s["h1"] or s["title"],
                          "provider": {"@id": ORG_ID}, "areaServed": {"@type": "City", "name": "Tarnów"}, "description": s["description"],
                          "url": prod_url(path)}]
                if s["faq"]:
                    graph.append({"@type": "FAQPage", "mainEntity": [{"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in s["faq"]]})
        elif path in DEMO_BLOG:
            robots = "noindex,follow"
        elif path.startswith("porady/") and path != "porady/":
            og_type = "article"
            text = set_title(text, fit_title(get_title(text).split(" | ")[0]))
            h1 = re.search(r"<h1>(.*?)</h1>", text, flags=re.S)
            img = re.search(r'<img[^>]+src="([^"]+)"', text[text.find('<main'):])
            image = prod_url(to_path(img.group(1))) if img and img.group(1).startswith(PREFIX) else OG_DEFAULT
            graph = [{"@type": "BlogPosting", "headline": html.unescape(re.sub("<.*?>", "", h1.group(1))) if h1 else get_title(text),
                      "image": image, "author": {"@id": ORG_ID}, "publisher": {"@id": ORG_ID}, "inLanguage": "pl-PL", "mainEntityOfPage": prod_url(path)}]
        elif path in ("promocje/", "najczesciej-kupowane/", "nowe-produkty/"):
            robots = "noindex,follow"
        elif path == "nota-prawna/":
            body = ('<p><strong>Pogotowie Akumulatorowe</strong></p>'
                    f'<p>E-mail: <a href="mailto:{EMAIL}">{EMAIL}</a><br/>Telefon: <a href="tel:{PHONE}">{PHONE_DISPLAY}</a></p>'
                    "<h2>Sklepy</h2><ul>" + "".join(f'<li>{esc(l["street"])}, {l["zip"]} {esc(l["city"])}, tel. {l["phone_display"]}</li>' for l in LOCATIONS) + "</ul>")
            text = re.sub(r'<div class="information-copy"><div class="prose">.*?</div></div>', f'<div class="information-copy"><div class="prose">{body}</div></div>', text, count=1, flags=re.S)

        bc = breadcrumb_ld(crumbs)
        if bc:
            graph.append(bc)
        text = inject_head(text, head_block(path, text, og_type, image, graph, robots))
        if text != orig:
            write(page, text)
        if robots is None:
            sitemap.append(prod_url(path))

    write_static_files(sitemap)
    write_redirects()
    print(f"brand pages: {len(brand_meta)}, collection pages: {len(coll_meta)}, location pages: {len(LOCATIONS)}, "
          f"h1 fixes: {dup_h1_fixed}, sitemap urls: {len(sitemap)}")


def write_static_files(urls: list[str]) -> None:
    urls = sorted(set(urls), key=lambda u: (u.count("/"), u))
    write(SITE / "sitemap.xml", '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
          + "".join(f"<url><loc>{esc(u)}</loc></url>\n" for u in urls) + "</urlset>\n")
    write(SITE / "robots.txt", f"User-agent: *\nAllow: /\n\nSitemap: {PROD_ORIGIN}/sitemap.xml\n")
    loc_lines = "\n".join(f"- {l['street']}, {l['zip']} {l['city']}, tel. {l['phone_display']}: {PROD_ORIGIN}/nasze-sklepy/{l['slug']}/" for l in LOCATIONS)
    write(SITE / "llms.txt", f"# {BRAND} (Tarnów)\n\n> Sklep z akumulatorami i mobilne pogotowie akumulatorowe w Tarnowie i Radłowie: sprzedaż, dowóz, montaż, test i kodowanie akumulatorów.\n\n"
          f"Telefon: {PHONE_DISPLAY}. E-mail: {EMAIL}. Autoryzowana Stacja Obsługi Akumulatorów Banner.\n\n## Sklepy\n{loc_lines}\n\n"
          f"## Najważniejsze strony\n- Oferta: {PROD_ORIGIN}/oferta/\n- Marki: {PROD_ORIGIN}/marki/\n- Usługi: {PROD_ORIGIN}/uslugi/\n"
          f"- Pogotowie akumulatorowe: {PROD_ORIGIN}/uslugi/odpalenie-unieruchomionego-pojazdu/\n- Porady: {PROD_ORIGIN}/porady/\n"
          + "".join(f"- {c['h1']}: {PROD_ORIGIN}/oferta/{c['slug']}/\n" for c in COLLECTIONS
                    if (SITE / "oferta" / c["slug"] / "index.html").exists()) + "\n"
          "## Gratis\n" + "\n".join(f"- {s}" for s in FREE_SERVICES) + "\n")


if __name__ == "__main__":
    main()
