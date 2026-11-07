# Poprawki SEO i build produkcyjny

Skrypty wdrażają poprawki z audytu SEO z 2026-11-07 na statyczną stronę w `public/akumulatory-tarnow`.

## Uruchomienie

Polecenia uruchamiasz z katalogu głównego repo. Wymagany jest Python 3.11+ z pakietami beautifulsoup4 i Pillow.

```bash
python tools/seo/apply_seo.py
python tools/seo/build_production.py
```

- `apply_seo.py` poprawia pliki w `public/akumulatory-tarnow`:
  - tytuły, opisy i H1;
  - canonical, Open Graph i JSON-LD;
  - strony marek i trzech sklepów oraz stronę 404;
  - `sitemap.xml`, `robots.txt` i `llms.txt`;
  - `.htaccess` i `_redirects`;
  - obrazy logo;
  - poprawki CLS.

  Skrypt jest idempotentny: kolejne uruchomienie nie zmienia już żadnego pliku. Po każdej zmianie w `catalog-data.json` albo w stronach trzeba uruchomić go ponownie.
- `build_production.py` kopiuje stronę do `dist/akumulatory-tarnow-www` i usuwa prefiks GitHub Pages `/akumulatory-tarnow-v2/`. Kończy się błędem, jeśli prefiks gdzieś zostanie.
- Dane firmy, czyli sklepy, telefony, teksty usług i tytuły stron statycznych, są w `site_data.py`.

## Wdrożenie na akumulatory-tarnow.pl

1. Na serwer trafia cała zawartość `dist/akumulatory-tarnow-www`, razem z plikami ukrytymi `.htaccess` i `_redirects`.
2. Hosting musi obsługiwać przekierowania 301 po stronie serwera:
   - Apache lub LiteSpeed korzysta z `.htaccess`;
   - Netlify i Cloudflare Pages korzystają z `_redirects`.

   Goły GitHub Pages ich nie obsługuje.
3. Przekierowania mają zostać na serwerze co najmniej 12 miesięcy. Jest ich 445. Każde wskazuje istniejącą stronę bez dalszego przekierowania.
4. Po przełączeniu domeny:
   - zgłoś `https://www.akumulatory-tarnow.pl/sitemap.xml` w Google Search Console;
   - obserwuj raporty „Strony” i „Mapy witryn” oraz błędy 404.

## Dane do potwierdzenia u klienta

- Godziny otwarcia sklepów. Strona ich jeszcze nie podaje. Wizytówki Google mają je od 2026-11-07, zobacz `akumulatory-tarnow-maps/MAPS-ANALYSIS-akumulatory-tarnow.pl.md`; przed wpisaniem trzeba je potwierdzić.
- Numer domu na Giełdowej. Strona podaje 5, wizytówka Google 6, a pod numerem 5 jest w Google i w OSM sklep Agadar, 3 m obok.
- Radłów. Wizytówka Google istnieje (CID 4499867822145091107), ale podaje telefon 609 734 290 (strona: 601 519 142) i linkuje do nieistniejącej domeny `akumulatorytarnow.pl`.
- NIP, pełna nazwa firmy i adres siedziby do noty prawnej.
- Biegun w danych katalogu. Filtr `biegun` podaje „Prawy +”, a indeks producenta wskazuje lewy plus w produktach:
  - 194 (GJ100L+);
  - 200 (GJE70L+);
  - 245 (Y3J60L+).

  Dopóki to nie jest potwierdzone, tytuły tych par rozróżnia indeks.
- Produkt 204 ma w nazwie „45AH 440A”, a w parametrach 42 Ah i 390 A.
- Produkt 67 (Ładowarka BOSCH C3) ma stronę, ale nie ma go w `catalog-data.json` i nic do niego nie linkuje. Czy jest jeszcze w sprzedaży?
