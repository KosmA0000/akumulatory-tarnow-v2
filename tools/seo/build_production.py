"""Buduje wersję produkcyjną pod https://www.akumulatory-tarnow.pl/ (katalog główny domeny).

Kopiuje public/akumulatory-tarnow do dist/akumulatory-tarnow-www i usuwa prefiks repozytorium
GitHub Pages (/akumulatory-tarnow-v2/) ze wszystkich plików tekstowych. Canonicale, sitemap
i robots.txt już wskazują na domenę produkcyjną.

Uruchomienie (z katalogu repo):  python tools/seo/build_production.py
Wynik wgraj na serwer klienta razem z plikiem .htaccess (przekierowania 301).
"""
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SRC = REPO / "public" / "akumulatory-tarnow"
OUT = REPO / "dist" / "akumulatory-tarnow-www"
PREFIX = "/akumulatory-tarnow-v2/"
TEXT = {".html", ".css", ".js", ".mjs", ".json", ".xml", ".txt", ".webmanifest", ""}

if OUT.exists():
    shutil.rmtree(OUT)
shutil.copytree(SRC, OUT)
changed = 0
for f in OUT.rglob("*"):
    if f.is_file() and (f.suffix in TEXT or f.name in (".htaccess", "_redirects")):
        t = f.read_text(encoding="utf-8")
        n = t.replace(PREFIX, "/").replace("\\/akumulatory-tarnow-v2\\/", "\\/")  # także forma w wyrażeniach regularnych JS
        if n != t:
            f.write_text(n, encoding="utf-8", newline="\n")
            changed += 1
left = [str(f.relative_to(OUT)) for f in OUT.rglob("*") if f.is_file() and f.suffix in TEXT
        and "akumulatory-tarnow-v2" in f.read_text(encoding="utf-8", errors="ignore")]
print(f"zbudowano {OUT} | plików ze zmienionym prefiksem: {changed} | pozostałe wystąpienia prefiksu: {len(left)}")
if left:
    print("\n".join(left[:20]))
    sys.exit(1)
