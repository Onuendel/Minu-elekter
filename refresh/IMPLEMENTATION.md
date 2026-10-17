# Minu Elekter — GitHubi ettevalmistus

## Käivitamine

Vajalik Python 3.12 ja ajavööndite andmebaas (Linuxis tavaliselt olemas).

```sh
python3 refresh/verify.py
python3 -m unittest discover -s refresh -p 'test_*.py'
python3 refresh/sheet_plan.py --sheet-values refresh/sample.json --first-row 6002 --first-day 2026-09-08 --now 2026-09-09T12:00:00+03:00
```

Näidiskäsu tulemus: viimane täielik päev 2026-09-08, puuduvad päevad ja muudatused tühjad. Näidis sisaldab ainult ühte päeva, mitte kogu masterdata't.

## Sisend ja muudatuste plaan

Sheetsi adapter loeb **eksporditud JSON väärtusi**, mitte Google API-t. Anna A:K andmeread ilma kahe päisereata ning ekspordi tegelik algusrida. Kogu 2026 auditis kasuta kõiki andmeridu ja first-day 2026-01-01; päevade puudumist otsitakse ka ajaloo keskelt.

Ajatempel võib olla DD.MM.YYYY HH:MM või ISO koos UTC nihkega. Korduva sügisese ja olematu kevadise kohaliku tunni puhul katkestatakse töö, kui nihe puudub. Olemasolevat tabelit ei muudeta selleks automaatselt.

Valikuline `--incoming` on JSON loend: iga element sisaldab date, total_kwh ja points. Iga punkt sisaldab start (UTC nihkega), duration_minutes (15 või 60), kwh (arv), actual (boolean). See on meie sisendleping, **mitte väide Elektrilevi tegeliku JSON skeemi kohta**.

Väljund sisaldab kontrollitavaid D:E vahemikke, vanu ja uusi väärtusi. See ei kirjuta andmeid. Puuduva ettevalmistatud rea korral töö peatub; read, hinnad ja valemid ei teki oletuste põhjal.

## Enne päris kirjutamist

1. Ühenda testitud Elektrilevi andmehange; kontrolli rolli Kai Küttis ja õiget mõõtepunkti. Autentimise saladusi ei logita ega lisata hoidlasse.
2. Loe täpne Google Sheet ja valemid uuesti. Kontrolli börsihinna ühikuid ning maksude alust, säilita ajaloolised lepinguhinnad.
3. Näita kasutajale konkreetsed muudatused ja küsi luba. Enne kirjutamist võrdle lähteväärtusi uuesti; muutuse korral genereeri uus plaan. Serialiseeri kirjutamised, et kaks värskendust ei jookseks korraga.
4. Kirjuta alles seejärel kinnitatud vahemikud ning loe tulemus üle.
5. Dashboardi muutmine ja avaldamine vajavad eraldi kasutaja luba.

## Cloudflare

See pakett ei ole Cloudflare Worker ega valmis veebirakendus. Worki brauseriseanss ei ole automaatselt dashboardi nupust käivitatav. Enne Cloudflare'i juurutust tuleb valida ja päriselt testida autentimisega andmehanketeenus, Google ligipääs ning serveripoolne turvaline käivitus. Saladusi ei panda HTML-i ega GitHubi failidesse. Supabase'i, cron'i ega tasulisi teenuseid praegu ei lisata.

GitHubi automaattestid kontrollivad ainult kohalikku loogikat. Need ei logi Elektrilevisse ega kirjuta Sheetsi.
