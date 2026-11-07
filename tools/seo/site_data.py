"""Stałe dane firmy i treści używane przez apply_seo.py.

Wszystkie fakty o usługach pochodzą z istniejących tekstów strony (O nas, Nasze Usługi).
Braki (godziny otwarcia, NIP, nazwa prawna) są celowo pominięte, nie zgadywane.
"""

PREFIX = "/akumulatory-tarnow-v2/"
PROD_ORIGIN = "https://www.akumulatory-tarnow.pl"
BRAND = "Pogotowie Akumulatorowe"
PHONE = "+48500399154"
PHONE_DISPLAY = "500 399 154"
EMAIL = "sklep.akumulatory24@gmail.com"
FACEBOOK = "https://www.facebook.com/105827195034209"
SUFFIX = " | Akumulatory Tarnów"

LOCATIONS = [
    {
        "slug": "tarnow-krakowska-150",
        "label": "Tarnów, ul. Krakowska 150",
        "street": "ul. Krakowska 150",
        "city": "Tarnów",
        "zip": "33-100",
        "phone": "+48500399154",
        "phone_display": "500 399 154",
        "gbp": "https://www.google.com/maps?cid=8585249746960888798&hl=pl",
        "map": "https://www.google.com/maps/dir/?api=1&destination=49.9996087,20.9566325&destination_place_id=ChIJJWB7mTqFPUcR3rOdgyjvJHc",
        "place_id": "ChIJJWB7mTqFPUcR3rOdgyjvJHc",
        "geo": (49.9996087, 20.9566325),
        # godziny z wizytówki Google (stan 2026-11-07, ustawia je właściciel)
        "hours": [
            {"days": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"], "label": "poniedziałek–piątek", "opens": "08:00", "closes": "17:00"},
            {"days": ["Saturday"], "label": "sobota", "opens": "08:00", "closes": "13:00"},
            {"days": ["Sunday"], "label": "niedziela", "opens": None, "closes": None},
        ],
    },
    {
        "slug": "tarnow-gieldowa-5",
        "label": "Tarnów, ul. Giełdowa 5",
        "street": "ul. Giełdowa 5",
        "city": "Tarnów",
        "zip": "33-100",
        "phone": "+48530697747",
        "phone_display": "530 697 747",
        "gbp": "https://www.google.com/maps?cid=16430378936170826862&hl=pl",
        "map": "https://www.google.com/maps/dir/?api=1&destination=50.0181467,20.9488393&destination_place_id=ChIJg6qbPNmFPUcRbsyFL5duBOQ",
        "place_id": "ChIJg6qbPNmFPUcRbsyFL5duBOQ",
        "geo": (50.0181467, 20.9488393),
        # godziny z wizytówki Google (stan 2026-11-07, ustawia je właściciel)
        "hours": [
            {"days": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"], "label": "poniedziałek–piątek", "opens": "07:00", "closes": "17:30"},
            {"days": ["Saturday", "Sunday"], "label": "sobota i niedziela", "opens": "07:00", "closes": "13:00"},
        ],
    },
    {
        "slug": "radlow-kolejowa-5",
        "label": "Radłów, ul. Kolejowa 5",
        "street": "ul. Kolejowa 5",
        "city": "Radłów",
        "zip": "33-130",
        "phone": "+48601519142",
        "phone_display": "601 519 142",
        "gbp": "https://www.google.com/maps?cid=4499867822145091107&hl=pl",
        "map": "https://www.google.com/maps/dir/?api=1&destination=50.0829816,20.8483892&destination_place_id=ChIJwTlaysWBPUcRIzYrY_G9cj4",
        "place_id": "ChIJwTlaysWBPUcRIzYrY_G9cj4",
        "geo": (50.0829816, 20.8483892),
        # godziny z wizytówki Google (stan 2026-11-07, ustawia je właściciel)
        "hours": [
            {"days": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"], "label": "poniedziałek–piątek", "opens": "08:00", "closes": "16:00"},
            {"days": ["Saturday"], "label": "sobota", "opens": "08:00", "closes": "12:00"},
            {"days": ["Sunday"], "label": "niedziela", "opens": None, "closes": None},
        ],
    },
]

# Usługi GRATIS ze strony O nas (cytat listy, bez zmian znaczenia).
FREE_SERVICES = [
    "pomiar sprawności starego akumulatora profesjonalnymi testerami z wydrukiem",
    "pomiar ładowania w pojeździe potwierdzony wydrukiem",
    "test rozrusznika potwierdzony wydrukiem",
    "demontaż i montaż akumulatora (przy odbiorze w sklepie stacjonarnym)",
    "wymiana akumulatora z podtrzymaniem napięcia (przy odbiorze w sklepie stacjonarnym)",
    "kodowanie, czyli dopisanie nowego akumulatora do komputera (przy odbiorze w sklepie stacjonarnym)",
    "bezpłatne badanie akumulatora przez okres gwarancyjny",
]

# Tytuły, opisy i H1 stron statycznych (ścieżka bez prefiksu).
PAGES = {
    "": {
        "title": "Akumulatory Tarnów – sklep i pogotowie akumulatorowe",
        "description": "Akumulatory samochodowe, motocyklowe i rolnicze w Tarnowie i Radłowie. Odpalanie auta, dowóz i montaż, bezpłatny test akumulatora z wydrukiem. Tel. 500 399 154.",
    },
    "oferta/": {
        "title": "Oferta akumulatorów – sklepy w Tarnowie i Radłowie",
        "description": "Akumulatory samochodowe, motocyklowe, rolnicze, żelowe i marine, prostowniki i urządzenia rozruchowe. Bezpłatny montaż przy odbiorze w sklepie w Tarnowie.",
    },
    "uslugi/": {
        "title": "Usługi akumulatorowe w Tarnowie – odpalanie, montaż, test",
        "description": "Odpalanie unieruchomionego auta, dowóz i montaż akumulatora, test akumulatora, alternatora i rozrusznika, kodowanie Start/Stop, ładowanie. Tarnów i okolice.",
    },
    "porady/": {
        "title": "Porady o akumulatorach – ładowanie, odpalanie, Start/Stop",
        "description": "Porady Pogotowia Akumulatorowego z Tarnowa: jak ładować akumulator, jak bezpiecznie odpalić auto i jaki akumulator wybrać do pojazdu z systemem Start/Stop.",
    },
    "o-nas/": {
        "title": "O nas – Pogotowie Akumulatorowe Tarnów",
        "description": "Centrum akumulatorowe w Tarnowie i Radłowie: Autoryzowana Stacja Obsługi Akumulatorów Banner, ponad 20 marek, mobilny serwis i bezpłatne testy z wydrukiem.",
    },
    "kontakt/": {
        "title": "Kontakt – Pogotowie Akumulatorowe Tarnów i Radłów",
        "description": "Zadzwoń: 500 399 154 (Krakowska 150), 530 697 747 (Giełdowa 5, Tarnów), 601 519 142 (Kolejowa 5, Radłów). E-mail: sklep.akumulatory24@gmail.com.",
    },
    "nasze-sklepy/": {
        "title": "Sklepy z akumulatorami – Tarnów i Radłów",
        "description": "Trzy sklepy Pogotowia Akumulatorowego: Tarnów, ul. Krakowska 150 i ul. Giełdowa 5 oraz Radłów, ul. Kolejowa 5. Adresy, telefony i dojazd.",
    },
    "marki/": {
        "title": "Marki akumulatorów – Varta, Yuasa, Jenox, Banner i inne",
        "description": "Akumulatory i prostowniki marek Varta, Yuasa, Jenox, Banner, Grom, Centra, Viking, CTEK, NOCO i innych w sklepach Pogotowia Akumulatorowego w Tarnowie.",
    },
    "nota-prawna/": {
        "title": "Nota prawna | Pogotowie Akumulatorowe",
        "description": "Nota prawna serwisu Pogotowia Akumulatorowego z Tarnowa: dane kontaktowe i adresy sklepów.",
    },
}

# Rozbudowa stron usług. Fakty wyłącznie z treści klienta; reszta to ogólna wiedza o akumulatorach.
SERVICES = {
    "odpalenie-unieruchomionego-pojazdu": {
        "title": "Pogotowie akumulatorowe Tarnów – odpalenie auta",
        "h1": "Pogotowie akumulatorowe – odpalenie unieruchomionego pojazdu",
        "description": "Pogotowie akumulatorowe w Tarnowie: odpalimy unieruchomiony samochód, zdiagnozujemy akumulator i sprawdzimy podzespoły. Zadzwoń: 500 399 154.",
        "sections": [
            ("Jak działa pogotowie akumulatorowe", "ol", [
                "Dzwonisz pod numer 500 399 154 i mówisz, gdzie stoi auto i co się dzieje, na przykład że rozrusznik nie kręci albo słychać tylko klikanie.",
                "Mobilny serwis przyjeżdża na miejsce na terenie Tarnowa i uruchamia pojazd.",
                "Diagnozujemy akumulator i sprawdzamy kondycję podzespołów, żeby ustalić, czy wystarczy ładowanie, czy akumulator trzeba wymienić.",
                "Jeśli potrzebny jest nowy akumulator, możemy go dowieźć i zamontować pod domem.",
            ]),
            ("Kiedy warto zadzwonić", "ul", [
                "silnik nie zapala po nocy na mrozie albo po dłuższym postoju,",
                "rozrusznik kręci wolno, a kontrolki przygasają przy próbie rozruchu,",
                "w aucie zostały włączone światła lub odbiornik i akumulator się rozładował,",
                "akumulator ma już kilka sezonów i coraz gorzej radzi sobie z rozruchem.",
            ]),
        ],
        "faq": [
            ("Czy po odpaleniu mogę od razu jechać?", "Zwykle tak. Mocno rozładowany akumulator może jednak nie wystarczyć do kolejnego rozruchu, dlatego po odpaleniu sprawdzamy jego stan i mówimy, czy wystarczy doładowanie, czy potrzebna jest wymiana."),
            ("Czy mogę sprawdzić akumulator przed zimą?", "Tak. W sklepie stacjonarnym test akumulatora jest bezpłatny i dostajesz papierowy wydruk z wynikiem."),
        ],
    },
    "transport-akumulatora-do-klienta-na-terenie-tarnowa": {
        "title": "Dostawa akumulatora w Tarnowie tego samego dnia",
        "h1": None,
        "description": "Dowieziemy zakupiony akumulator na terenie Tarnowa w tym samym dniu roboczym, w godzinach 8:00–17:00. Montaż pod domem do wyboru. Tel. 500 399 154.",
        "sections": [
            ("Jak zamówić dostawę", "ol", [
                "Zadzwoń pod 500 399 154 i podaj markę, model i rocznik auta albo parametry obecnego akumulatora.",
                "Dobierzemy akumulator z oferty i potwierdzimy koszt dostawy, który zależy od odległości.",
                "Dowozimy w tym samym dniu roboczym, w godzinach 8:00–17:00.",
                "Przy zakupie z dostawą możesz wybrać montaż pod domem.",
            ]),
        ],
        "faq": [
            ("Ile kosztuje dostawa?", "Cennik dostaw zależy od odległości. Koszt podamy przy zamówieniu telefonicznym."),
        ],
    },
    "montaz-zakupionego-akumulatora-na-terenie-tarnowa": {
        "title": "Montaż akumulatora w Tarnowie – bezpłatnie w sklepie",
        "h1": None,
        "description": "Kupując akumulator u nas możesz liczyć na wymianę. Przy odbiorze w sklepie montaż jest bezpłatny, a przy dostawie wybierz montaż pod domem. Tel. 500 399 154.",
        "sections": [
            ("Co obejmuje montaż przy odbiorze w sklepie", "ul", [
                "demontaż starego i montaż nowego akumulatora,",
                "wymianę z podtrzymaniem napięcia, żeby nie stracić ustawień elektroniki,",
                "kodowanie, czyli dopisanie nowego akumulatora do komputera w autach z systemem Start/Stop.",
            ]),
        ],
        "faq": [
            ("Co zrobić ze starym akumulatorem?", "Zużyty akumulator to odpad niebezpieczny i nie wolno go wyrzucać do zwykłych śmieci. Przy zakupie nowego oddaj stary w sklepie."),
        ],
    },
    "wymiana-akumulatora-z-podtrzymaniem-elektroniki": {
        "title": "Wymiana akumulatora z podtrzymaniem elektroniki – Tarnów",
        "h1": None,
        "description": "Wymiana akumulatora bez utraty kodu radia i ustawień elektroniki. Przy odbiorze w sklepie stacjonarnym w Tarnowie usługa jest bezpłatna. Tel. 500 399 154.",
        "sections": [
            ("Po co podtrzymywać napięcie przy wymianie", "ul", [
                "radio z kodem nie zablokuje się po odłączeniu akumulatora,",
                "nie stracisz zapisanych ustawień, na przykład stacji radiowych czy pamięci foteli,",
                "elektronika auta nie wymaga ponownej konfiguracji po wymianie.",
            ]),
        ],
        "faq": [
            ("Ile kosztuje wymiana z podtrzymaniem?", "Przy odbiorze akumulatora w naszym sklepie stacjonarnym wymiana z podtrzymaniem napięcia jest bezpłatna."),
        ],
    },
    "test-akumulatora": {
        "title": "Bezpłatny test akumulatora w Tarnowie z wydrukiem",
        "h1": None,
        "description": "Bezpłatny test akumulatora w sklepie stacjonarnym w Tarnowie. Certyfikowane testery i papierowy wydruk potwierdzający sprawność lub zużycie. Tel. 500 399 154.",
        "sections": [
            ("Kiedy zrobić test akumulatora", "ul", [
                "przed zimą, gdy akumulator ma za sobą kilka sezonów,",
                "gdy auto gorzej zapala albo rozrusznik kręci wolniej niż zwykle,",
                "po rozładowaniu, żeby sprawdzić, czy akumulator nadaje się do dalszej pracy,",
                "w okresie gwarancji: badanie akumulatora jest u nas bezpłatne przez cały okres gwarancyjny.",
            ]),
        ],
        "faq": [
            ("Po czym poznać, że akumulator jest zużyty?", "Typowe objawy to wolne kręcenie rozrusznika, przygasające kontrolki przy rozruchu i częste rozładowania. Pewność daje dopiero test testerem, a u nas dostajesz z niego wydruk."),
        ],
    },
    "test-alternatora-i-rozrusznika": {
        "title": "Test alternatora i rozrusznika w Tarnowie z wydrukiem",
        "h1": None,
        "description": "Sprawdzimy rozrusznik i ładowanie w pojeździe, a wynik potwierdzimy wydrukiem. Tak ustalisz, czy problem leży w akumulatorze, czy w alternatorze.",
        "sections": [
            ("Dlaczego warto sprawdzić alternator i rozrusznik", "ul", [
                "słabe ładowanie z alternatora rozładowuje nawet nowy akumulator,",
                "zużyty rozrusznik pobiera więcej prądu i utrudnia rozruch,",
                "test z wydrukiem pozwala uniknąć wymiany akumulatora, gdy przyczyna jest gdzie indziej.",
            ]),
        ],
        "faq": [],
    },
    "kodowanie-akumulatora": {
        "title": "Kodowanie akumulatora Start/Stop w Tarnowie",
        "h1": None,
        "description": "Dopisanie nowego akumulatora do komputera auta z systemem Start/Stop. Dla klientów kupujących akumulator w naszym sklepie kodowanie jest bezpłatne.",
        "sections": [
            ("Dlaczego kodowanie jest potrzebne", "ul", [
                "system zarządzania energią w autach ze Start/Stop dobiera ładowanie do stanu akumulatora,",
                "bez dopisania nowego akumulatora komputer może ładować go jak stary i skracać jego żywotność,",
                "kodowanie wykonujemy profesjonalnymi, certyfikowanymi testerami, bez wizyty w ASO.",
            ]),
        ],
        "faq": [],
    },
    "ladowanie-akumulatorow-serwis-pogwarancyjny": {
        "title": "Ładowanie akumulatorów i serwis pogwarancyjny – Tarnów",
        "h1": None,
        "description": "Profesjonalne ładowanie akumulatora z odsiarczaniem i przeglądem elektrolitu, w sklepie albo z odbiorem i dostawą pod dom. Tel. 500 399 154.",
        "sections": [
            ("Jak wygląda ładowanie z odbiorem", "ol", [
                "Odbieramy rozładowany akumulator.",
                "Wykonujemy przegląd stanu elektrolitu i ładowanie z funkcją odsiarczania.",
                "Dostarczamy naładowany akumulator z powrotem do Ciebie.",
            ]),
        ],
        "faq": [],
    },
}
