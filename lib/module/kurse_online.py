#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from lib.utils import dstr, p2k
from lib.kursedb import *
from lib.stammdaten import *
from lib.onlinekursabfrage.base import *
from lib.onlinekursabfrage import init_abfragemodule
from lib.messages import messages

import random, time

# Keys bei der Onvista-Online-Abfrage
OV_ONLINE_DATUM = "datum"
OV_ONLINE_LAST = "last"
OV_ONLINE_VOLUME = "volume"

def online_kurs_lookup(*, downloader, isin, abfragedatum, stammdaten, config):
    def testdate():
        nonlocal first
        nonlocal abfragedatum
        if first:
            print("   ^^^^^^^^^^^^^^^^     ", dstr(abfragedatum))
            first = False

    stamm_dat = stammdaten.get_entry(isin)
    assert stamm_dat is not None, f"{isin} nicht in Stammdaten"

    print("ISIN...:", isin)
    print("Name...:", stamm_dat[STAMMDATEN_NAME])
    print("Währung:", stamm_dat[STAMMDATEN_KURSWAEHRUNG])

    beginn = abfragedatum - datetime.timedelta(days=7)

    abfrager = init_abfragemodule(
        downloader=downloader,
        config=config,
        stammdaten=stammdaten
    )

    for qu in abfrager:
        print(">>> Abfrage", qu["name"])
        print("\nDatum              Schluss   Volumen")
        data = qu["poi"].query_isin(isin=isin, startdate=beginn)

        # print("Ergebnis Onlineabfrage:", data)

        first = True
        for item in data:
            thisdate = datetime.date(year=item["datum"].year, month=item["datum"].month,
                                    day=item["datum"].day)
            if thisdate > abfragedatum:
                testdate()
            print("%s %9.3f %7.1f" % (item["datum"].strftime("%d.%m.%Y %H:%M"), item["last"], item["volume"]))
            if thisdate == abfragedatum:
                testdate()


def refresh_datenbank(*, config, downloader, kursedb, stammdaten, ignore=None, verbose=False):
    # Initialisierung der Onlineabfrage

    abfrager = init_abfragemodule(
        downloader=downloader,
        config=config,
        stammdaten=stammdaten
    )

    for isin in kursedb.all_isins():
        print(isin, end=" ")

        res = stammdaten.get_entry(isin)
        if res is None:
            raise ValueError(f"*** {isin} nicht in Stammdaten")

        isin_name = res[STAMMDATEN_NAME]
        isin_waehrung = res[STAMMDATEN_KURSWAEHRUNG]
        print("- ", isin_name)

        if verbose:
            print("ISIN:", isin, "-", isin_name)
            print("interne Nummer", kursedb.isin2index(isin))

        last = kursedb.get_last_kurs(isin)
        letztes_datum = last[KURSEDB_DATUM]
        letzter_kurs = last[KURSEDB_SCHLUSSKURS]

        if verbose:
            print("last:", last)

        for qu in abfrager:
            if verbose:
                print("* Abfrage", qu["name"])

            # zufällige Wartezeit zwischen zwei Abfragen,
            # um Website nicht zu überlasten

            s = 7 + random.random() * 7.0
            print("* Warte %.1f s" % s)
            time.sleep(s)

            try:
                data = qu["poi"].query_isin(isin=isin, startdate=letztes_datum)
            except FehlendeISINAbfrageParameterException as msg:
                messages.warning(msg)
                continue

            if verbose:
                print("Ergebnis Onlineabfrage:", data)

            anz_kurse = len(data)
            if anz_kurse == 0:
                messages.warning(f"* {qu['name']} gibt keine Kurse für {isin} zurück")
                # Versuche nächsten abfrager
                continue

            if anz_kurse == 1:
                # Es wurden Kurse zurückgegeben, aber nur der mit dem letzten Datum
                # => keine neuen Kurse
                break

            while True:
                # Es wurden mehrere Kurse zurückgegeben
                # Prüfe, ob der erste zurückgegebene mit dem letzten
                # gespeicherten Kurs übereinstimmt
                first_date = data[0][KURSABFRAGE_DATUM].date()
                first_kurs = data[0][KURSABFRAGE_LAST]

                if (letztes_datum != first_date) or (letzter_kurs != first_kurs):
                    # Fehler: Debug-Ausgabe
                    # ak = kursedb.get_alle_kurse(isin)
                    # for item in ak:
                    #     print(item[KURSEDB_DATUM].strftime("%d.%m.%Y"), item[KURSEDB_SCHLUSSKURS])

                    abw = abs(letzter_kurs-first_kurs)

                    if verbose:
                        print("%s (intern %s): %s" % (isin, kursedb.isin2index(isin), isin_name))
                        print("Anschluss stimmt nicht")
                        print("Datenbank.:", dstr(letztes_datum), letzter_kurs)
                        print("Online....:", dstr(first_date), first_kurs)
                        print("Abweichung:", p2k(abw))
                        print("Ignoriere.:", ignore)

                    if (ignore is not None) and (abw <= ignore):
                        messages.warning("Ignoriere Unstimmigkeit beim Anschluss von %s: %s" % (
                            isin,
                            p2k(abw)
                        ))
                    else:
                        raise ValueError("Anschluss nicht möglich bei %s, Abweichung %s" % (
                            isin,
                            p2k(abw)
                        ))

                # Bestimme neue Daten
                if verbose:
                    print("letztes Datum:", letztes_datum, letzter_kurs)

                neue_daten = []
                for item in data:
                      if item[OV_ONLINE_DATUM].date() > letztes_datum:
                        neu = {
                            KURSEDB_DATUM: item [OV_ONLINE_DATUM],
                            KURSEDB_SCHLUSSKURS: item[OV_ONLINE_LAST],
                            KURSEDB_VOLUMEN: item[OV_ONLINE_VOLUME]
                        }
                        neue_daten.append(neu)
                        if verbose:
                            print(neu)

                if verbose:
                    print("ISIN............:", isin)
                    print("Einträge vorher.:", kursedb.count_kurse())
                    print("Anzahl neu......:", len(neue_daten))
                    print("Neue Daten......:", neue_daten)

                # speichere neue Daten in Datenbank
                kursedb.insert_kurse(isin, datalist=neue_daten)
                if verbose:
                    print("Einträge nachher:", kursedb.count_kurse())
                    res = stammdaten.get_entry(isin)
                    print(isin_name)
                    print(isin_waehrung)

                # Suche (neues) Anschlussdatum in der Datenbank
                k = kursedb.get_last_kurs(isin)
                letztes_datum = k[KURSEDB_DATUM]
                letzter_kurs = k[KURSEDB_SCHLUSSKURS]

                data = qu["poi"].query_isin(isin=isin, startdate=letztes_datum)
                anz_kurse = len(data)
                if anz_kurse <= 1:
                    break
            break

