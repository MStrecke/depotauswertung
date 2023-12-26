#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
from .utils import dparse
from .yamlbase import YamlBase
from .depot import Depot_Stammdaten
from lib.isincheck import isin_check

# Der Aufbau von Portfolio- und Ausschüttungsdaten ist nahezu identisch:
#
# * Ausschüttung fehlt "anzahl" (definitionsgemäß 1)
# * der Wert von "Betrag" wird in "kurs" gespeichert
#
# Die "Transaktion" hat keine ISIN, weil sie als Untermenge aller Transaktionen gefiltert
# nach eben dieser ISIN erzeugt wird.

AUSSCHUETTUNG_ISIN = "isin"
PORTFOLIO_ISIN = "isin"

TRANSAKTION_ANZAHL = "anzahl"
TRANSAKTION_KURS = "kurs"
TRANSAKTION_DATUM = "datum"
TRANSAKTION_TYP = "typ"
TRANSAKTION_TYP_KAUF = "kauf"
TRANSAKTION_TYP_VERKAUF = "verkauf"
TRANSAKTION_TYP_UEBERTRAG = "übertrag"
TRANSAKTION_TYP_AUSSCHUETTUNG = "ausschuettung"
TRANSAKTION_DEPOT = "depot"
TRANSAKTION_WAEHRUNG = "waehrung"

AUSSCHUETTUNG_BETRAG = "betrag"      # nur bei Ausschüttungen

dcom = re.compile("(\d{1,2}).(\d{1,2}).(\d\d\d\d)")

def _yaml_reorder(yamldat):
    """ Erzeugung eines Key zum Sortieren der Einträge

    :param s: daten
    :type s: yaml-Eintrag
    :return: Sortierwert
    :rtype: str
    """
    # Sortiertwert: YYYYMMDD_ISIN_DEPOT
    ma = dcom.match(yamldat["datum"])
    assert ma is not None, "unpassender Wert: " + yamldat
    datum = "%s%02d%02d" % (ma.group(3), int(ma.group(2)), int(ma.group(1)))
    return "%s_%s_%s" % (datum, yamldat["isin"], yamldat["depot"])

DATUM_CO = re.compile("^\d{1,2}\.\d{1,2}\.\d{4}$")
BETRAG_CO = re.compile("^[.,0-9]+$")

class Transaktionen(YamlBase):
    def __init__(self, portfolio_filename:str, ausschuettung_filename:str, *, depots:Depot_Stammdaten, isinliste):
        """ Transaktionen

        :param portfolio_filename: Yaml-Datei mit den Käufen und Verkäufen
        :type portfolio_filename: str
        :param ausschuettung_filename: Yaml-Datei mit den Ausschüttungen
        :type ausschuettung_filename: str
        :param depots: Depot-Klasse
        :type depots: Depot_Stammdaten
        :param isinliste: Liste der ISINs aus den Stammdaten
        :type depotliste: list[str]
        """
        self.portfolio = YamlBase(portfolio_filename, [PORTFOLIO_ISIN, TRANSAKTION_TYP, TRANSAKTION_DEPOT, TRANSAKTION_DATUM, TRANSAKTION_ANZAHL, TRANSAKTION_WAEHRUNG])
        self.ausschuettung = YamlBase(ausschuettung_filename, [AUSSCHUETTUNG_ISIN, TRANSAKTION_DATUM, TRANSAKTION_DEPOT, AUSSCHUETTUNG_BETRAG, TRANSAKTION_TYP])
        self.depots = depots
        self.isinliste = isinliste

    def check_mandatory_entries(self):
        self.portfolio.check_mandatory_entries()
        self.ausschuettung.check_mandatory_entries()

    def base_check(self):
        super().base_check()
        depotliste = self.depots.get_alle_depots()

        for item in self.portfolio.iter_entries():
            self.regex_check(item, TRANSAKTION_DATUM, DATUM_CO)
            datum = item[TRANSAKTION_DATUM]
            # Prüfziffer
            isin_check.check_list(item[PORTFOLIO_ISIN])
            # in Stammdaten
            self.content_must_be(item, PORTFOLIO_ISIN, self.isinliste)
            info = datum + " " + item[PORTFOLIO_ISIN]
            self.content_must_be(item, TRANSAKTION_TYP, [TRANSAKTION_TYP_KAUF, TRANSAKTION_TYP_VERKAUF], info=info, fkt=lambda x:x.lower())
            self.content_must_be(item, TRANSAKTION_DEPOT, depotliste, info=info)
            self.content_not_empty(item, TRANSAKTION_WAEHRUNG, info=info)
            self.regex_check(item, TRANSAKTION_KURS, BETRAG_CO, info=info)
            self.regex_check(item, TRANSAKTION_ANZAHL, BETRAG_CO, info=info)

        for item in self.ausschuettung.iter_entries():
            self.regex_check(item, TRANSAKTION_DATUM, DATUM_CO)
            datum = item[TRANSAKTION_DATUM]
            isin_check.check_list(item[AUSSCHUETTUNG_ISIN])
            self.content_must_be(item, AUSSCHUETTUNG_ISIN, self.isinliste)
            info = datum + " " + item[AUSSCHUETTUNG_ISIN]
            self.content_must_be(item, TRANSAKTION_TYP, [TRANSAKTION_TYP_AUSSCHUETTUNG], fkt=lambda x:x.lower())
            self.content_must_be(item, TRANSAKTION_DEPOT, depotliste, info=info)
            self.content_not_empty(item, TRANSAKTION_WAEHRUNG, info=info)
            self.regex_check(item, AUSSCHUETTUNG_BETRAG, BETRAG_CO, info=info)


    def get_isin_depot_list(self):
        """ Gebe sortierte Liste aller Tuples aus (depot, isin) zurück

        :return: (depot, isin)
        :rtype: list
        """
        res = []
        for item in self.portfolio.iter_entries():
            dat = (item[TRANSAKTION_DEPOT], item[PORTFOLIO_ISIN])
            if not dat in res:
                res.append(dat)

        for item in self.ausschuettung.iter_entries():
            dat = (item[TRANSAKTION_DEPOT], item[AUSSCHUETTUNG_ISIN])
            if not dat in res:
                res.append(dat)

        return sorted(res)

    def get_by_isin(self, isin, *, depot=None, start=None, ende=None):
        def dat_check_ok(s:str) -> bool:
            dat = dparse(s)
            if start is not None:
                if dat < start:
                    return False
            if ende is not None:
                if dat > ende:
                    return False
            return True

        checkdate = start is not None or ende is not None

        result = []
        for item in self.portfolio.iter_entries():
            assert item[TRANSAKTION_TYP] in [TRANSAKTION_TYP_KAUF, TRANSAKTION_TYP_VERKAUF]

            if item[PORTFOLIO_ISIN] != isin:
                continue

            if (depot is not None):
                if (item[TRANSAKTION_DEPOT] != depot):
                    continue
                if self.depots.get_depotwaehrung(depot) != item[TRANSAKTION_WAEHRUNG]:
                    raise ValueError("Portfolio- und Depotwährung stimmen nicht überein (%s / %s)" % (
                        item[TRANSAKTION_WAEHRUNG],
                        self.depots.get_depotwaehrung(depot)
                    ))

            if checkdate:
                if not dat_check_ok(item[TRANSAKTION_DATUM]):
                    continue

            result.append(item)

        for item in self.ausschuettung.iter_entries():
            if item[AUSSCHUETTUNG_ISIN] == isin:
                assert item[TRANSAKTION_TYP] in [TRANSAKTION_TYP_AUSSCHUETTUNG]

            if item[AUSSCHUETTUNG_ISIN] != isin:
                continue

            if (depot is not None):
                if (item[TRANSAKTION_DEPOT] != depot):
                    continue
                if self.depots.get_depotwaehrung(depot) != item[TRANSAKTION_WAEHRUNG]:
                    raise ValueError("Ausschüttungs- und Depotwährung stimmen nicht überein (%s / %s)" % (
                        item[TRANSAKTION_WAEHRUNG],
                        self.depots.get_depotwaehrung(depot)
                    ))

            if checkdate:
                if not dat_check_ok(item[TRANSAKTION_DATUM]):
                    continue

            result.append(item)

        res2 = sorted(result, key=lambda x: _yaml_reorder(x))
        return res2