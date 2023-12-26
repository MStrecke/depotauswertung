#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Dieses Modul ist dafür gedacht die Transaktionen INNERHALB EINES JAHRS zu betrachten und
dient damit zur Ermittlung des Basisertrags.

- Der Basisertrag fällt nicht an, wenn der Anteil in diesem Jahr verkauft wird.
- Er fällt nur anteilig an, wenn der Anteil unterjährig gekauft wird:
  - Feb: -1/12, März: -2/12 ...
- Ausschüttungen werden aufsummiert.

Die Bewertung erfolgt zum Schluss und gibt die diversen Summen zurück für die übergeordnete
Prozedur zurück.


Mögliche Transaktionen:
-----------------------
TRANSAKTION_TYP_UEBERTRAG
   Wenn vorhanden, muss dies die erste Transaktion sein.
   Sie setzt die Anzahl der Anteile zu Beginn des Jahres.

TRANSAKTION_TYP_KAUF
   Stellt einen Ankauf von Anteilen dar.

TRANSAKTION_TYP_VERKAUF
   Stelle einen Verkauf von Anteilen dar.

   Die Anzahl wird von den ältesten Tranchen (UEBERTRAG bzw. KAUF) abgezogen.

TRANSAKTION_TYP_AUSSCHUETTUNG
   Stellte eine Ausschüttung dar.

Beispiel:
    jt = JahresTranchen()
    jt.set_uebertrag(dparse("01.01.2022"), 50, 100)
    jt.kauf(dparse("01.03.2022"), 20, 110)
    jt.ausschuettung(dparse("10.03.2022"), 10.00)
    jt.verkauf(dparse("01.04.2022"), 55, 110)
    jt.ausschuettung(dparse("01.06.2022"), 5.10)
    jt.kauf(dparse("01.07.2022"), 55, 120)
    res = jt.bewertung(2022, 100, 120, 2.55, verbose=True)
    print(res)
"""
from .utils import myround, dstr, p2k, k2p, dparse
from .transaktionen import *
from .vorabpauschale import get_basiszins_proz, monatsanteil
from .kursedb import KURSEDB_SCHLUSSKURS

import datetime

# TRANSAKTION_TYP_UEBERTRAG = "Übertrag"
# TRANSAKTION_TYP_KAUF = "Kauf"
# TRANSAKTION_TYP_VERKAUF = "Verkauf"
# TRANSAKTION_TYP_AUSSCHUETTUNG = "Ausschüttung"

BEW_ITEMS = "items"
BEW_SUMME_BASISERTRAG = "summe_basisertrag"
BEW_SUMME_AUSSCHUETTUNGEN = "summe_ausschuettungen"
BEW_SUMME_WERTSTEIGERUNG = "summe_wertsteigerung"
BEW_SUMME_WERT_ANFANG = "summe_wert_anfang"
BEW_SUMME_WERT_ENDE = "summe_wert_ende"
BEW_VERKAEUFE_IM_JAHR = "verkäufe_im_jahr"

class TransaktionNichtChronologischException(ValueError): pass
class TransaktionImFalschenJahrException(ValueError): pass
class ZuVielVerkauftException(ValueError): pass
class UnbekannteTransaktionException(ValueError): pass

class Transaktion:
    """ Diese Klasse speichert die Daten einer Transaktion

        Sie kennt keine ISIN.

        Sie kennt die Typen TRANSAKTION_TYP_UEBERTRAG, TRANSAKTION_TYP_KAUF, TRANSAKTION_TYP_VERKAUF, TRANSAKTION_TYP_AUSSCHUETTUNG und setzt
        die Werte entsprechend.

        start_anzahl      Wert, wenn die Transaktion angelegt wird
        variable_anzahl   Wert, wird durch Verkäufe reduziert
                          Beim Anlegen:
                             TRANSAKTION_TYP_KAUF/TRANSAKTION_TYP_UEBERTRAG: anzahl
                             sonst None
    """
    def __init__(self, typ:str, datum:datetime.date, anzahl:float, kurs_zum_datum:float, waehrungsfaktor_zum_datum:float):
        self.typ = typ
        self.datum = datum
        self.start_anzahl = anzahl

        # Anzahl, die von Verkäufen beeinflusst wird
        if self.typ in [TRANSAKTION_TYP_UEBERTRAG, TRANSAKTION_TYP_KAUF]:
            self.variable_anzahl = anzahl     #  dieser Wert wird durch Verkäufe gemindert
        elif self.typ in [TRANSAKTION_TYP_VERKAUF, TRANSAKTION_TYP_AUSSCHUETTUNG]:
            self.variable_anzahl = None       # ein Dummy-Wert
        else:
            raise ValueError(f"Unbekannter Transaktions: {typ}")

        self.kurs_zum_datum = kurs_zum_datum       # oder Ausschüttungsbetrag bei TRANSAKTION_TYP_AUSSCHUETTUNG
        self.waehrungsfaktor = waehrungsfaktor_zum_datum   # bei Fonds in USD
        self.monatsanteil = monatsanteil(datum)

        # Diese werden erst zum Schluss berechnet
        self.basisertrag = None
        self.wert_ende = None
        self.wertsteigerung = None

class Transaktionen:
    """ Diese Klasse speichert eine Liste von Transaktionen.

        Sie wird normalerweise pro ISIN/Depot angelegt, kennt aber keine ISINs.
        Mit `jahr` != None wird eine Überprüfung des Transaktionsdatums aktiviert.

        Die kennt die Funktionen: kauf, verkauf und ausschuettung

        `anzahl_anteile_gesamt` wird entsprechend Kauf/Verkauf aktualisiert.

        `verkauf` reduziert die Variable `variable_anzahl` der vorhergehenden Kauf/Übertrags-
        Transaktionen, sodass `variable_anzahl` die noch verbleibenden Anteile für diese
        Transaktion zu diesem Zeitpunkt wiederspiegelt.
    """
    def __init__(self, jahr=None):
        # Liste der Transaktion
        self.transaktionen = []

        # Prüfe, ob Transaktion in diesem Jahr
        # None = keine Prüfung (jahresübergreifend)
        self.jahr = jahr

        # Datum der letzten Transaktion (nur chronologisch erlaubt)
        self.last_date = None

        # Summe aller Anteile dieser ISIN
        self.anzahl_anteile_gesamt = 0

    def _add_transaktion(self, typ:str, datum:datetime.date, anzahl:float, kurs_zum_datum:float, waehrungsfaktor_zum_datum:float):
        # Sicherstellen, dass Tranchen chronologisch hinzukommen
        if (self.last_date is not None) and (self.last_date > datum):
            raise TransaktionNichtChronologischException(
                "Transaktionen nicht chronologisch: %s > %s" % (dstr(self.last_date), dstr(datum))
            )

        if self.jahr is not None and (datum.year != self.jahr):
            raise TransaktionImFalschenJahrException("Transaktion vom %s nicht im Jahr %s" % (
                dstr(datum),
                self.jahr
            ))

        self.last_date = datum

        jt = Transaktion(typ,
                         datum=datum,
                         anzahl=anzahl,
                         kurs_zum_datum=kurs_zum_datum,
                         waehrungsfaktor_zum_datum=waehrungsfaktor_zum_datum)
        self.transaktionen.append(jt)

    def ausschuettung(self, datum:datetime.date, betrag:float, waehrungsfaktor_zum_datum:float):
        self._add_transaktion(TRANSAKTION_TYP_AUSSCHUETTUNG,
                              datum=datum,
                              anzahl=1,
                              kurs_zum_datum=betrag,
                              waehrungsfaktor_zum_datum=waehrungsfaktor_zum_datum)

    def kauf(self, datum:datetime.date, anzahl:float, kurs_zum_datum:float, waehrungsfaktor_zum_datum:float):
        self.anzahl_anteile_gesamt += anzahl
        self._add_transaktion(TRANSAKTION_TYP_KAUF,
                              datum=datum,
                              anzahl=anzahl,
                              kurs_zum_datum=kurs_zum_datum,
                              waehrungsfaktor_zum_datum=waehrungsfaktor_zum_datum)

    def verkauf(self, datum:datetime.date, anzahl:float, kurs_zum_datum:float, waehrungsfaktor_zum_datum:float):
        self.anzahl_anteile_gesamt -= anzahl
        self._add_transaktion(TRANSAKTION_TYP_VERKAUF,
                              datum=datum,
                              anzahl=-anzahl,
                              kurs_zum_datum=kurs_zum_datum,
                              waehrungsfaktor_zum_datum=waehrungsfaktor_zum_datum)

        # Verkauf von bisherigen Käufen abziehen
        #
        # TRANSAKTION_TYP_KAUF ist ein "normaler" Kauf.
        # TRANSAKTION_TYP_UEBERTRAG wird nur verwendet, wenn nur die Transaktionen innerhalb
        # eines Jahres betrachtet werden. Es beschreibt den Bestand am Jahresanfang
        # und ist (falls verwendet) immer die erste Transaktion.
        # In diesem Zusammenhang ist es ein "spezieller" Kauf, von dem zuerst
        # der Verkauf abgezogen wird.

        for transaktion in self.transaktionen:
            # Nur von Übertrag oder Käufen abziehen
            if transaktion.typ not in [TRANSAKTION_TYP_UEBERTRAG, TRANSAKTION_TYP_KAUF]:
                continue

            # Man kann nur verkaufen, was man gekauft hat
            assert transaktion.datum < datum

            # `anzahl` beschreibt die noch zu verteilende Menge
            if anzahl > transaktion.variable_anzahl:
                anzahl -= transaktion.variable_anzahl
                transaktion.variable_anzahl = 0
            else:
                transaktion.variable_anzahl -= anzahl
                anzahl = 0

            if anzahl == 0:
                break

        if anzahl != 0:
            raise ZuVielVerkauftException("Mehr Anteile verkauft als vorhanden %s" % anzahl)

class JahresTransaktionen(Transaktionen):
    """
    Die Jahrestransaktionen unterscheiden sich von den "normalen" Transaktionen
    darin, dass sie nur Transaktionen eines Jahrs aufnehmen (d.h. jahr ist nicht None)

    Sie haben zusätzlich die Funktion `set_uebertrag`, der den Bestand am Jahresanfang
    definiert und - falls verwendet - die erste Transaktion überhaupt sein muss.
    (Da beim Verkauf die Anteile zuerst dort abgezogen werden)
    """

    def __init__(self, jahr:int):
        assert jahr is not None, "Jahr muss gesetzt sein"

        super().__init__(jahr)
        self.uebertrag_done = False

    def set_uebertrag(self, datum:datetime.date, anzahl:float, kurs_zum_datum:float, waehrungsfaktor_zum_datum:float):
        # Übertrag darf nur einmal auftreten
        assert self.uebertrag_done is False

        # und dann auch nur ganz am Anfang
        assert len(self.transaktionen) == 0

        self.anzahl_anteile_gesamt = anzahl

        self._add_transaktion(TRANSAKTION_TYP_UEBERTRAG,
                              datum=datum,
                              anzahl=anzahl,
                              kurs_zum_datum=kurs_zum_datum,
                              waehrungsfaktor_zum_datum=waehrungsfaktor_zum_datum)
        self.uebertrag_done = True

    def do_transaktionen(self, *, fondwaehrung, transaktionen, kursedb):
        waehrungsconv = "EUR" + fondwaehrung
        for transaktion in transaktionen:
            waehrungsfaktor_zum_datum = 1.0
            if waehrungsconv != "EUREUR":
                waehrungsfaktor_zum_datum = 1.0 / kursedb.get_kurs(waehrungsconv,dparse(transaktion[TRANSAKTION_DATUM]))[KURSEDB_SCHLUSSKURS]

            if transaktion[TRANSAKTION_TYP] == TRANSAKTION_TYP_KAUF:
                self.kauf(
                    datum=dparse(transaktion[TRANSAKTION_DATUM]),
                    anzahl=k2p(transaktion[TRANSAKTION_ANZAHL]),
                    kurs_zum_datum=k2p(transaktion[TRANSAKTION_KURS]),
                    waehrungsfaktor_zum_datum=waehrungsfaktor_zum_datum
                    )
            elif transaktion[TRANSAKTION_TYP] == TRANSAKTION_TYP_VERKAUF:
                self.verkauf(
                    datum=dparse(transaktion[TRANSAKTION_DATUM]),
                    anzahl=k2p(transaktion[TRANSAKTION_ANZAHL]),
                    kurs_zum_datum=k2p(transaktion[TRANSAKTION_KURS]),
                    waehrungsfaktor_zum_datum=waehrungsfaktor_zum_datum
                    )
            elif transaktion[TRANSAKTION_TYP] == TRANSAKTION_TYP_AUSSCHUETTUNG:
                self.ausschuettung(
                    datum=dparse(transaktion[TRANSAKTION_DATUM]),
                    betrag=k2p(transaktion[AUSSCHUETTUNG_BETRAG]),
                    waehrungsfaktor_zum_datum=waehrungsfaktor_zum_datum
                )
            else:
                raise UnbekannteTransaktionException("Unbekannte Transaktion: "+transaktion[TRANSAKTION_TYP])


    def bewertung(self, *, jahr:int, jahresstartkurs:float, jahresendkurs:float,
                  waehrungsfaktor_jahresanfang:float, waehrungsfaktor_last:float,
                  kurswaehrung:str,
                  verbose=False):
        # Die Bewertung wird normalerweise zum Jahresende vorgenommen.
        #
        # Erst zu diesem Zeitpunkt ist klar:
        # * wie viele Anteile von den Kauf-Transaktionen noch übrig sind
        # * wie hoch der Kurs zum Jahresende ist
        #
        # Sie nimmt NICHT vor:
        # * den Abzug der Teilstellung
        # * die Abwägung der Vorabpauschale zwischen Ausschüttungen, Basiserträgen und Wertsteigerung
        #
        # Berechnung des Basisertrags
        # ---------------------------
        #
        # Beim Basisertrags werden nur die Anteile berücksichtigt, die am Jahresende noch da sind.
        # (Verkaufte Anteile unterliegen nicht der Vorabpauschale, da sie der normalen Versteuerung
        # unterliegen).
        # Aber
        # * es wird immer den Kurs vom Jahresanfang verwendet, auch wenn der Kauf unterjährig stattfand
        # * wenn der Kauf unterjährig stattfand, wird der Betrag anteilig vermindert (volle Monate vor Kauf)
        #
        # D.h., für alle TRANSAKTION_TYP_KAUF und den TRANSAKTION_TYP_UEBERTRAG wird aufsummiert
        # Anzahl noch verbliebende Anteile * jahresstartkurs * 0,7
        #
        # Ermittlung der Wertsteigerung
        # -----------------------------
        #
        # Die Ermittlung findet nur für ein bestimmtes Jahr statt.
        #
        # Berücksichtigt werden nur die Transaktionen TRANSAKTION_TYP_KAUF und TRANSAKTION_TYP_UEBERTRAG. Und dort nur die
        # "noch verbliebenden" Anteile (`variable_anzahl`).
        #
        # Wert am Jahresende = Anzahl noch verbliebende Anteile * Kurs zum Jahresende * waehrungsfaktor zum Jahresende
        # Anfangswert = Anzahl noch verbliebende Anteile * Kurs beim Kauf (falls unterjährig) bzw.
        # der vom Jahresanfang ("Kaufkurs" in TRANSAKTION_TYP_UEBERTRAG) * waehrungsfaktor zu diesem Tag.
        #
        # Die Summen berechnen sich also für alle TRANSAKTION_TYP_KAUF und TRANSAKTION_TYP_UEBERTRAG summierten `Wert am Jahresende`
        # und `Anfangswert`.
        #
        # Summe der Ausschüttungen
        # ------------------------
        # Summiert einfach die ausgeschütteten Beträge (die in `kurs_zum_datum` gespeichert sind.)

        basiszins_proz = get_basiszins_proz(jahr)

        if verbose:
            print("Kurs - Start/Ende: %s / %s" % (
                p2k(jahresstartkurs,4),
                p2k(jahresendkurs,4)))
            if waehrungsfaktor_jahresanfang != 1 or waehrungsfaktor_last != 1:
                print("Währungsfaktoren - Start/Ende: %s / %s" % (
                    p2k(waehrungsfaktor_jahresanfang),
                    p2k(waehrungsfaktor_last)
                ))
            print("Basiszins: %s%%" % p2k(basiszins_proz,2))

        verkaeufe_im_jahr = False

        # Der Zustand dieser Transaktionen ist der am Ende des Jahres,
        # d.h. `variable_anzahl` spiegelt den Zustand nach allen Verkäufen wieder
        for item in self.transaktionen:
            if item.typ in [TRANSAKTION_TYP_KAUF, TRANSAKTION_TYP_UEBERTRAG]:
                # Beim Übertrag und Kauf wird ein Basisertrag ermittelt
                # Er basiert auf den Papieren, die am Ende des Jahres noch vorhanden
                # sind, jedoch mit dem Kurs vom Jahresanfang
                item.basisertrag = myround(item.variable_anzahl * jahresstartkurs * 0.7 * basiszins_proz / 100.0 * item.monatsanteil * waehrungsfaktor_jahresanfang,2)
                # Der Anfangswert sind die verbliebenen Anteile zum Tageskurs und Tageswechselkurs
                item.wert_anfang = myround(item.variable_anzahl * item.kurs_zum_datum * item.waehrungsfaktor,2)
                # Der Endwert sind die am Jahresende verbleibenen Anteil zum Kurs + Währungskurs am Jahresende
                item.wert_ende = myround(jahresendkurs * item.variable_anzahl * waehrungsfaktor_last,2)
                item.wertsteigerung = item.wert_ende - item.wert_anfang
            elif item.typ == TRANSAKTION_TYP_AUSSCHUETTUNG:
                item.basisertrag = None
                item.wertsteigerung = None
                item.wert_anfang = None
                item.wert_ende = None
            elif item.typ == TRANSAKTION_TYP_VERKAUF:
                item.basisertrag = None
                item.wertsteigerung = None
                item.wert_anfang = None
                item.wert_ende = None
                verkaeufe_im_jahr = True

        if verbose:
            print("Typ           Datum         Anzahl   RestAnz        kurs      Wert-A    Wert-E  Wertzuw.  Basisertrag Monatsanteil Währungsfakt.")
            print("                                                     %s         EUR       EUR       EUR          EUR" % kurswaehrung)

        res = {
            "items": []
        }
        summe_basisertrag = 0.0
        summe_wertsteigerung = 0.0
        summe_ausschuettungen = 0.0
        summe_wert_anfang = 0.0
        summe_wert_ende = 0.0

        for item in self.transaktionen:
            # Summiere Basisertrag
            if item.basisertrag is not None:
                summe_basisertrag += item.basisertrag
            # Summiere Wertsteigerung
            if item.wertsteigerung is not None:
                summe_wertsteigerung += item.wertsteigerung
            # Summiere Ausschüttungen
            if item.typ == TRANSAKTION_TYP_AUSSCHUETTUNG:
                summe_ausschuettungen += myround(item.kurs_zum_datum * item.waehrungsfaktor,2)
            # Summiere Anfangswerte
            if item.wert_anfang is not None:
                summe_wert_anfang += item.wert_anfang
            # Summiere Endwerte
            if item.wert_ende is not None:
                summe_wert_ende += item.wert_ende

            res[BEW_ITEMS].append(item)
            if verbose:
                if item.typ != TRANSAKTION_TYP_AUSSCHUETTUNG:
                    if item.typ != TRANSAKTION_TYP_VERKAUF:
                        endwert = myround(item.variable_anzahl * jahresendkurs * waehrungsfaktor_last,2)
                    else:
                        endwert = None
                    print("%-13s %s %9s %9s %11s %11s %9s %9s %9s %9s %16s" % (
                    item.typ,
                    dstr(item.datum),
                    p2k(item.start_anzahl,4),
                    p2k(item.variable_anzahl,4),
                    p2k(item.kurs_zum_datum,4),
                    p2k(item.wert_anfang,2),
                    p2k(endwert,2),
                    p2k(item.wertsteigerung,2),
                    p2k(item.basisertrag,2),
                    int(item.monatsanteil*12.0+0.1),
                    p2k(item.waehrungsfaktor)
                    ))
                else:
                    print("%-12s %s %14s %9s %75s" % (
                    item.typ,
                    dstr(item.datum),
                    p2k(item.kurs_zum_datum,2),
                    p2k(item.kurs_zum_datum * item.waehrungsfaktor,2),
                    p2k(item.waehrungsfaktor)
                    ))

        if verbose:
            print("\n  Summen %24s %15s %18s %9s %9s %9s" % (
                p2k(self.anzahl_anteile_gesamt,4),
                p2k(summe_ausschuettungen,2),
                p2k(summe_wert_anfang,2),
                p2k(summe_wert_ende,2),
                p2k(summe_wertsteigerung,2),
                p2k(summe_basisertrag,2),
            ))
            if summe_wert_anfang != 0:
                p = summe_wertsteigerung / summe_wert_anfang * 100.0
                print("%88s %%" % p2k(p,2,sign=True))

        res[BEW_SUMME_BASISERTRAG] = myround(summe_basisertrag,2)
        res[BEW_SUMME_WERTSTEIGERUNG] = myround(summe_wertsteigerung,2)
        res[BEW_SUMME_AUSSCHUETTUNGEN] = myround(summe_ausschuettungen,2)
        res[BEW_SUMME_WERT_ANFANG] = myround(summe_wert_anfang,2)
        res[BEW_SUMME_WERT_ENDE] = myround(summe_wert_ende,2)
        res[BEW_VERKAEUFE_IM_JAHR] = myround(verkaeufe_im_jahr,2)
        return res

if __name__ == "__main__":
    if False:
        jt = JahresTransaktionen()
        jt.set_uebertrag(dparse("01.01.2022"), 50, 100)
        jt.kauf(dparse("01.03.2022"), 20, 110)
        jt.ausschuettung(dparse("10.03.2022"), 10.00)
        jt.verkauf(dparse("01.04.2022"), 55, 110)
        jt.ausschuettung(dparse("01.06.2022"), 5.10)
        # jt.kauf(dparse("01.07.2022"), 55, 120)
        res = jt.bewertung(100, 120, 2.55, verbose=True)
        print(res)