#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from lib.transaktionen import *
from lib.utils import dstr, p2k, k2p, myround
from lib.vorabpauschale import get_basiszins_proz
from lib.kursedb import *
from lib.stammdaten import *
from lib.tranche import *

import datetime

BEWERTUNGSWAEHRUNG = "EUR"

def berechne_realisierte_GuV(*, isin:str, depot:str, jahr:int, transaktionen, kursedb) -> float:
    # Für alle Transaktionen einer bestimmten ISIN in einem Depot:
    #  * die einzelnen Käufe merken.
    #  * bei Verkäufen, Anteile von den Käufen abziehen und Gewinn merken, falls im angegebenen Jahr

    summe_gewinn_im_jahr = 0.0

    kaeufe = []
    for item in transaktionen.get_by_isin(isin, depot=depot):
        ttyp = item[TRANSAKTION_TYP].lower()
        tdatum = dparse(item[TRANSAKTION_DATUM])
        if ttyp == TRANSAKTION_TYP_KAUF:
            wfaktor = kursedb.get_waehrungs_faktor(item[TRANSAKTION_WAEHRUNG], BEWERTUNGSWAEHRUNG, tdatum)
            tr = Transaktion(
                typ=TRANSAKTION_TYP_KAUF,
                datum=tdatum,
                anzahl=k2p(item[TRANSAKTION_ANZAHL]),
                kurs_zum_datum=k2p(item[TRANSAKTION_KURS]),
                waehrungsfaktor_zum_datum=wfaktor
            )
            kaeufe.append(tr)
        elif ttyp == TRANSAKTION_TYP_VERKAUF:
            # suche zugehörige Tranche
            verkaufs_rest = k2p(item[TRANSAKTION_ANZAHL])
            verkaufs_kurs = k2p(item[TRANSAKTION_KURS])
            for kauf in kaeufe:
                if kauf.variable_anzahl == 0:
                    continue
                hiervon = min(kauf.variable_anzahl, verkaufs_rest)
                einkauf = myround(kauf.kurs_zum_datum * hiervon, 2)
                verkauf = myround(verkaufs_kurs * hiervon, 2)
                gewinn = myround(verkauf-einkauf,2)
                summe_gewinn_im_jahr += gewinn

                if tdatum.year == jahr:
                    d = {
                        "anzahl": hiervon,
                        "einkaufsdatum": kauf.datum,
                        "einkaufskurs": kauf.kurs_zum_datum,
                        "einkaufswert": einkauf,
                        "verkaufsdatum": tdatum,
                        "verkaufskurs": verkaufs_kurs,
                        "verkaufswert": verkauf
                    }
                    print("%s: %s aus Tranche vom %s zum Kurs von %s = %s - %s = %s" %
                        (
                            dstr(d["verkaufsdatum"]),
                            p2k(d["anzahl"], 4),
                            dstr(d["einkaufsdatum"]),
                            p2k(d["einkaufskurs"],4),
                            p2k(d["einkaufswert"],2),
                            p2k(d["verkaufswert"], 2),
                            p2k(gewinn)
                        ))

                kauf.variable_anzahl -= hiervon
                verkaufs_rest -= hiervon
                if verkaufs_rest == 0:
                    break

            assert verkaufs_rest == 0

    return summe_gewinn_im_jahr

def do_vorabpauschale(isin:str, depot:str, jahr:int, stammdaten, transaktionen, kursedb):
    def line_out(item):
        if item.typ == TRANSAKTION_TYP_AUSSCHUETTUNG:
            print("%s %-13s %9s %15s" % (
                dstr(item.datum),
                item.typ,
                "",
                p2k(item.kurs_zum_datum, 4)), # 4
            )
        else:
            print("%s %-13s %9s %9s %9s %9s %9s %9s %9s %2d" % (
                dstr(item.datum),
                item.typ,
                # Start/Jahresanfang
                p2k(item.start_anzahl, 4),
                p2k(item.kurs_zum_datum, 4), # 4
                p2k(item.wert_anfang,2),
                p2k(item.variable_anzahl, 4), # 4
                p2k(item.wert_ende, 2), #2
                p2k(item.wertsteigerung, 2),
                p2k(item.basisertrag, 2),
                int(item.monatsanteil * 12.0 + 0.1)
            ))



    basiszins_proz = get_basiszins_proz(jahr)

    jahresstart = datetime.date(year=jahr, month=1, day=1)
    jahresende = datetime.date(year=jahr, month=12, day=31)

    stammdat = stammdaten.get_entry(isin)
    assert stammdat is not None, "Keine Daten zu "+ isin

    kurs_waehrung = stammdat[STAMMDATEN_KURSWAEHRUNG]

    teilfreistellung = stammdat.get(STAMMDATEN_TEILFREISTELLUNG)
    if teilfreistellung is None:
        ValueError("Teilfreistellungsangabe fehlt für " + isin)
    assert teilfreistellung.endswith("%")

    # Teilfreistellung gibt es erst seit 2018
    if jahresstart.year < 2018:
        teilfreistellung_faktor = 0.0
    else:
        teilfreistellung_faktor = float(teilfreistellung[:-1].replace(",",".")) / 100.0

    # Bestimme Anzahl der Anteil zu Jahresbeginn
    anteile_jahresanfang = 0.0
    first = True
    for item in transaktionen.get_by_isin(isin, depot=depot):
        first = False
        da = dparse(item[TRANSAKTION_DATUM])
        if da < jahresstart:
            if item[TRANSAKTION_TYP] == TRANSAKTION_TYP_KAUF:
                anteile_jahresanfang += k2p(item["anzahl"])
            elif item[TRANSAKTION_TYP] == TRANSAKTION_TYP_VERKAUF:
                anteile_jahresanfang -= k2p(item["anzahl"])
            elif item[TRANSAKTION_TYP] == TRANSAKTION_TYP_AUSSCHUETTUNG:
                continue
            else:
                raise ValueError("ungültige Transaktion: "+item[TRANSAKTION_TYP])
        else:
            break

    if first:
        raise ValueError("Keine Daten vorhanden für %s" % isin)

    print("ISIN ...........:", isin)
    print("Name ...........:", stammdat[STAMMDATEN_NAME])
    print("Depot ..........:", depot)
    print("Währung ........:", kurs_waehrung)
    print("Teilfreistellung:", teilfreistellung)
    print("Jahr ...........:", jahr)
    print("Basiszins ......: %s%%" % p2k(basiszins_proz,2))

    alletrans = transaktionen.get_by_isin(isin, depot=depot, start=jahresstart, ende=jahresende)

    if anteile_jahresanfang == 0.0:
        # Vorabcheck, ob in diesem Jahr Transaktionen stattgefunden haben
        if len(alletrans) == 0:
            print("\n\n*** Keine Transaktionen in diesem Jahr")
            return None

    # Bestimme Kurs zu Jahresbeginn
    jahresanfang = kursedb.get_kurs(isin, jahresstart)
    assert jahresanfang is not None, "Keine Kursdaten für " + isin
    kurs_jahresanfang = jahresanfang[KURSEDB_SCHLUSSKURS]
    waehrungsfaktor_jahresanfang = kursedb.get_waehrungs_faktor(kurs_waehrung, BEWERTUNGSWAEHRUNG, jahresstart)

    # Bestimme letzten Kurs, des Jahres
    kursedat_last = kursedb.get_kurs(isin, jahresende)
    kurs_last = kursedat_last[KURSEDB_SCHLUSSKURS]
    kurs_last_datum = kursedat_last[KURSEDB_DATUM]
    waehrungsfaktor_last = kursedb.get_waehrungs_faktor(kurs_waehrung, BEWERTUNGSWAEHRUNG, kurs_last_datum)


    print("Letzter Kurs vom:", dstr(kurs_last_datum), "-", p2k(kurs_last,4))
    print()
    print("Datum       Transaktion   Anzahl-S    Kurs-S    Wert-S  Anzahl-E    Wert-E   Wertst.     Vorab Mo")
    print("                                       %s        %s                 %s       %s       %s\n" % (
        kurs_waehrung,
        BEWERTUNGSWAEHRUNG,
        BEWERTUNGSWAEHRUNG,
        BEWERTUNGSWAEHRUNG,
        BEWERTUNGSWAEHRUNG
        ))

    ja = JahresTransaktionen(jahr)
    ja.set_uebertrag(
        datum=jahresstart,
        anzahl=anteile_jahresanfang,
        kurs_zum_datum=kurs_jahresanfang,
        waehrungsfaktor_zum_datum=waehrungsfaktor_jahresanfang
    )
    ja.do_transaktionen(transaktionen=alletrans,
                        fondwaehrung=kurs_waehrung,
                        kursedb=kursedb)
    res = ja.bewertung(
        jahr=jahr,
        jahresstartkurs=kurs_jahresanfang,
        jahresendkurs=kurs_last,
        waehrungsfaktor_jahresanfang=waehrungsfaktor_jahresanfang,
        waehrungsfaktor_last=waehrungsfaktor_last,
        kurswaehrung=kurs_waehrung,
        verbose=False
    )

    summe_basisertrag = res[BEW_SUMME_BASISERTRAG]
    summe_wertsteigerung = res[BEW_SUMME_WERTSTEIGERUNG]
    summe_wert_anfang = res[BEW_SUMME_WERT_ANFANG]
    summe_wert_ende = res[BEW_SUMME_WERT_ENDE]
    summe_ausschuettungen = res[BEW_SUMME_AUSSCHUETTUNGEN]

    for item in res[BEW_ITEMS]:
        line_out(item)

    print()
    if summe_wert_anfang != 0:
        wsp = summe_wertsteigerung / summe_wert_anfang * 100.0
    else:
        wsp = None

    print("Summen %47s %8s%% %9s %9s %9s" % (p2k(summe_wert_anfang, 2), p2k(wsp,1, sign=True), p2k(summe_wert_ende,2), p2k(summe_wertsteigerung,2), p2k(summe_basisertrag,2)))
    if summe_ausschuettungen != 0:
        print("           Ausschüttungen: %21s" % p2k(summe_ausschuettungen,2))

    # Die Vorabpausche wird hier berechnet.
    # Bis jetzt wurde nur die Teil-Basiserträge, die Teil-Wertsteigerungen und Teil-Ausschüttungen
    # aufsummiert

    vorab = summe_basisertrag

    # Wenn die tatsächliche Wertsteigerung geringer ist,
    # wird diese verwendet
    if summe_wertsteigerung < vorab:
        vorab = summe_wertsteigerung

    # Beträge, die wegen Ausschüttungen sowieso versteuert werden,
    # werden von der Vorabpauschale abgezogen

    vorab -= summe_ausschuettungen
    if vorab < 0:
        vorab = 0

    # Hier stehen nun die zu versteuernden Summen fest, die aber
    # noch um die Teilfreistellung gemindert werden.

    vorab_bemessung = myround(vorab * (1.0-teilfreistellung_faktor),2)

    # Das gilt auch für die Ausschüttungen
    sum_ausschuettungen_bemessung = myround(summe_ausschuettungen * (1.0-teilfreistellung_faktor),2)

    if sum_ausschuettungen_bemessung == 0.0:
        print("Bemessung\n           Vorabpauschale: %10s" % (p2k(vorab_bemessung,2),))
    else:
        print("Bemessung\n           Vorab/Auschütt: %10s %10s" % (p2k(vorab_bemessung,2), p2k(sum_ausschuettungen_bemessung,2)))

    realisiert = None
    if res[BEW_VERKAEUFE_IM_JAHR]:
        print("\n\nVerkäufe im Jahr")
        realisiert = berechne_realisierte_GuV(
            isin=isin,
            depot=depot,
            jahr=jahr,
            transaktionen=transaktionen,
            kursedb=kursedb
            )

    return {
        "isin": isin,
        "depot": depot,
        "bemessung_vorabpauschale": vorab_bemessung,
        "ausschuettungen": summe_ausschuettungen,
        "bemessung_ausschüttungen": sum_ausschuettungen_bemessung,
        "wert": summe_wert_anfang,
        "wertsteigerung": summe_wertsteigerung,
        "realisiert": realisiert
    }

def do_vorabpauschale_jahr(*, isin, jahr:int, depot:str, transaktionen, stammdaten, kursedb):

    assert isin_check.check_list(isin)

    if isin is not None:
        entry = stammdaten.get_entry(isin)
        assert entry is not None, "* Keine Stammdaten für %s" % isin   # sollte nicht vorkommen

    allres = []
    for item in transaktionen.get_isin_depot_list():
        if isin is not None:
            if isin != item[1]:
                continue
        if depot is not None:
            if depot != item[0]:
                continue
        res = do_vorabpauschale(item[1], item[0], jahr,
                                stammdaten=stammdaten,
                                transaktionen=transaktionen,
                                kursedb=kursedb)
        if res is not None:
            allres.append(res)
        print("="*70)

    summe_bemessung_vorab = 0.0
    summe_wert_anfang = 0.0
    summe_wertsteigerung = 0.0
    summe_bemessung_ausschuettung = 0.0
    summe_realisiert = 0.0

    print("ISIN         Depot   Vorabpauschale Ausschütt-Bemes Wert Steigerung Realisiert Name")
    print("                              %s        %s        %s        %s        %s\n" % (
        BEWERTUNGSWAEHRUNG, BEWERTUNGSWAEHRUNG, BEWERTUNGSWAEHRUNG, BEWERTUNGSWAEHRUNG, BEWERTUNGSWAEHRUNG
    ))
    for item in allres:
        name = stammdaten.get_entry(item["isin"])[STAMMDATEN_NAME]
        print("%-10s %-10s %10s %10s %10s %10s %10s %s" %(
            item["isin"],
            item["depot"],
            p2k(item["bemessung_vorabpauschale"],2),
            p2k(item["bemessung_ausschüttungen"],2),
            p2k(item["wert"],2),
            p2k(item["wertsteigerung"],2),
            p2k(item["realisiert"], 2),
            name
        )
        )

        realisiert = item["realisiert"]
        if realisiert is not None:
            summe_realisiert += realisiert

        summe_bemessung_vorab += item["bemessung_vorabpauschale"]
        summe_wert_anfang += item["wert"]
        summe_wertsteigerung += item["wertsteigerung"]
        summe_bemessung_ausschuettung += item["bemessung_ausschüttungen"]

    print()
    print("Summen %27s %10s %10s %10s %10s" % (
        p2k(summe_bemessung_vorab,2),
        p2k(summe_bemessung_ausschuettung,2),
        p2k(summe_wert_anfang,2),
        p2k(summe_wertsteigerung,2),
        p2k(summe_realisiert,2)
    ))

