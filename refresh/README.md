# Minu Elekter: värskenduse kontrollmoodul

Eraldi prototüüp. Ei muuda Google Sheetsi ega olemasolevat dashboardi.

Käivita `python3 verify.py`. Kasutab ainult Pythoni standardteeki.

Valmis: mõõtepunktide täielikkuse kontroll, 15 minuti koguste summeerimine, Eesti ajavöönd, 23/25 tunni päevad, duplikaatide tõrje, puuduvate päevade leidmine, muudatuste plaan, hinnavõrdlus marginaaliga.

Kontrollandmed: Google Sheeti Data 2026 read 6002–6025, 08.09.2026. Kogus 17,313 kWh võrdub Elektrilevi UI-st loetuga. See ei tõesta veel automaatset Elektrilevi allalaadimist ega JSON-adapterit.

Veel tegemata: Elektrilevi andmete adapter, Sheetsi ajatemplite üheseks teisendamine ja kirjutamise adapter, börsihinna allikas ning maksude/ühikute kontroll, dashboardi värskendusteenus ja turvaline autentimine. Cloud Browseri vestluses toimiv juhtimine ei ole iseenesest veebirakendusest väljakutsutav API.

Olemasolevad ajaloolised lepinguhinnad tuleb säilitada. Sügisese korduva tunni võti peab sisaldama UTC aega või UTC nihet. Puuduv kogus ei ole null, tekst Tegelik üksi ei tõesta täielikkust. Mõõtepunkti adapter peab eristama tegelikke mõõtmisi prognoosidest.
