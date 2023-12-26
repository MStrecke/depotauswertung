#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest
import os

import lib.config
import lib.isincheck
import lib.utils
import lib.tranche
import lib.vorabpauschale
import lib.stammdaten
import lib.depot
import lib.transaktionen
import lib.kursedb

class TestIsinCheck(unittest.TestCase):
    def setUp(self):
        self.isincheck = lib.isincheck.isin_check

    def test_isin(self):
        self.assertTrue(self.isincheck.check("LU1437016972"))
        self.assertFalse(self.isincheck.check("LU1437016973"))
        self.assertTrue(self.isincheck.check_list("LU1437016972"))
        self.assertTrue(self.isincheck.check_list(["LU1437016972"]))
        self.assertFalse(self.isincheck.check_list(["LU1437016972", "LU1437016973"], verbose=False))

    def test_utils(self):
        self.assertEqual(lib.utils.dstr(None), "????")
        d = lib.utils.dparse("1.2.2013")
        self.assertEqual(lib.utils.dstr(d), "01.02.2013")
        d = lib.utils.dparse("21.12.2014")
        self.assertEqual(lib.utils.dstr(d), "21.12.2014")

        self.assertEqual(lib.utils.my_sign(-3.3), -1)
        self.assertEqual(lib.utils.my_sign(4.3), 1)
        self.assertEqual(lib.utils.my_sign(0), 0)

        self.assertEqual(lib.utils.myround(1.2341,4), 1.2341)
        self.assertEqual(lib.utils.myround(1.2341,3), 1.234)
        self.assertEqual(lib.utils.myround(1.2345,3), 1.235)
        self.assertEqual(lib.utils.myround(-1.2341,3), -1.234)
        self.assertEqual(lib.utils.myround(-1.2345,3), -1.235)

        self.assertEqual(lib.utils.k2p("-1,234"), -1.234)
        self.assertEqual(lib.utils.k2p("1,234"), 1.234)
        self.assertEqual(lib.utils.k2p("1.234,5"), 1234.5)

        self.assertEqual(lib.utils.p2k(None), "-")
        self.assertEqual(lib.utils.p2k(1), "1")
        self.assertEqual(lib.utils.p2k(1, 2), "1,00")
        self.assertEqual(lib.utils.p2k(1.005, 2), "1,01")
        self.assertEqual(lib.utils.p2k(-1.005, 2), "-1,01")

    def test_transaktionen(self):
        d = lib.tranche.Transaktionen()
        d.kauf(lib.utils.dparse("1.2.2018"), 10, 100, 1.0)     # 0
        self.assertEqual(d.anzahl_anteile_gesamt, 10)
        d.kauf(lib.utils.dparse("1.3.2018"), 10, 105, 1.0)     # 1
        self.assertEqual(d.anzahl_anteile_gesamt, 20)
        d.verkauf(lib.utils.dparse("1.4.2018"), 15, 110, 1.0)  # 2
        self.assertEqual(d.anzahl_anteile_gesamt, 5)
        self.assertEqual(d.transaktionen[0].start_anzahl, 10)
        self.assertEqual(d.transaktionen[0].variable_anzahl, 0)
        self.assertEqual(d.transaktionen[1].start_anzahl, 10)
        self.assertEqual(d.transaktionen[1].variable_anzahl, 5)

        # UnbekannteTransaktionException
        self.assertRaises(lib.tranche.TransaktionNichtChronologischException, d.verkauf, lib.utils.dparse("1.1.2018"), 10, 110, 1.0)
        self.assertRaises(lib.tranche.ZuVielVerkauftException, d.verkauf, lib.utils.dparse("1.5.2018"), 10, 110, 1.0)

    def test_bewertung_eur(self):
        jt = lib.tranche.JahresTransaktionen(2018)
        self.assertRaises(lib.tranche.TransaktionImFalschenJahrException, jt.set_uebertrag, lib.utils.dparse("1.1.2019"), 10, 110, 1.0)
        jt.set_uebertrag(lib.utils.dparse("1.1.2018"), 10, 100, 1.0)  # 0
        self.assertEqual(jt.anzahl_anteile_gesamt, 10)
        jt.kauf(lib.utils.dparse("1.3.2018"), 10, 105, 1.0)           # 1
        self.assertEqual(jt.anzahl_anteile_gesamt, 20)
        jt.verkauf(lib.utils.dparse("1.4.2018"), 15, 110, 1.0)        # 2
        self.assertEqual(jt.anzahl_anteile_gesamt, 5)
        jt.ausschuettung(lib.utils.dparse("01.06.2018"), 5.10, 1.0)   # 3
        jt.ausschuettung(lib.utils.dparse("01.09.2018"), 6.10, 1.0)   # 3

        self.assertEqual(lib.vorabpauschale.get_basiszins_proz(2018), 0.87)

        res = jt.bewertung(
            jahr=2018,
            jahresstartkurs=100,
            jahresendkurs=120,
            waehrungsfaktor_jahresanfang=1.0,
            waehrungsfaktor_last=1.0,
            kurswaehrung="EUR",
            verbose=False)
        self.assertEqual(res[lib.tranche.BEW_SUMME_BASISERTRAG], 2.54)
        self.assertEqual(res[lib.tranche.BEW_SUMME_WERTSTEIGERUNG], 75.00)
        self.assertEqual(res[lib.tranche.BEW_SUMME_AUSSCHUETTUNGEN], 11.20)
        self.assertEqual(res[lib.tranche.BEW_SUMME_WERT_ANFANG], 525.00)
        self.assertEqual(res[lib.tranche.BEW_SUMME_WERT_ENDE], 600.00)

    def test_bewertung_usd(self):
        jt = lib.tranche.JahresTransaktionen(2018)
        self.assertRaises(lib.tranche.TransaktionImFalschenJahrException, jt.set_uebertrag, lib.utils.dparse("1.1.2019"), 10, 110, 1.0)
        jt.set_uebertrag(lib.utils.dparse("1.1.2018"), 10, 100, 1.1)  # 0
        self.assertEqual(jt.anzahl_anteile_gesamt, 10)
        jt.kauf(lib.utils.dparse("1.3.2018"), 10, 105, 1.2)           # 1
        self.assertEqual(jt.anzahl_anteile_gesamt, 20)
        jt.verkauf(lib.utils.dparse("1.4.2018"), 15, 110, 1.3)        # 2
        self.assertEqual(jt.anzahl_anteile_gesamt, 5)
        jt.ausschuettung(lib.utils.dparse("01.06.2018"), 5.10, 1.35)   # 3
        jt.ausschuettung(lib.utils.dparse("01.09.2018"), 6.10, 1.36)   # 3

        res = jt.bewertung(
            jahr=2018,
            jahresstartkurs=100,
            jahresendkurs=120,
            waehrungsfaktor_jahresanfang=1.1,
            waehrungsfaktor_last=1.4,
            kurswaehrung="XYZ",
            verbose=False)
        self.assertEqual(res[lib.tranche.BEW_SUMME_BASISERTRAG], 2.79)
        self.assertEqual(res[lib.tranche.BEW_SUMME_WERTSTEIGERUNG], 210.00)
        self.assertEqual(res[lib.tranche.BEW_SUMME_AUSSCHUETTUNGEN], 15.19)
        self.assertEqual(res[lib.tranche.BEW_SUMME_WERT_ANFANG], 630.00)
        self.assertEqual(res[lib.tranche.BEW_SUMME_WERT_ENDE], 840.00)

    def test_bewertung_usd_rest_uebertrag(self):
        jt = lib.tranche.JahresTransaktionen(2018)
        self.assertRaises(lib.tranche.TransaktionImFalschenJahrException, jt.set_uebertrag, lib.utils.dparse("1.1.2019"), 10, 110, 1.0)
        jt.set_uebertrag(lib.utils.dparse("1.1.2018"), 10, 100, 1.1)  # 0
        self.assertEqual(jt.anzahl_anteile_gesamt, 10)
        jt.kauf(lib.utils.dparse("1.3.2018"), 10, 105, 1.2)           # 1
        self.assertEqual(jt.anzahl_anteile_gesamt, 20)
        jt.verkauf(lib.utils.dparse("1.4.2018"), 5, 110, 1.3)        # 2
        self.assertEqual(jt.anzahl_anteile_gesamt, 15)
        jt.ausschuettung(lib.utils.dparse("01.06.2018"), 5.10, 1.35)   # 3
        jt.ausschuettung(lib.utils.dparse("01.09.2018"), 6.10, 1.36)   # 3

        res = jt.bewertung(
            jahr=2018,
            jahresstartkurs=100,
            jahresendkurs=120,
            waehrungsfaktor_jahresanfang=1.1,
            waehrungsfaktor_last=1.4,
            kurswaehrung="XYZ",
            verbose=False)
        self.assertEqual(res[lib.tranche.BEW_SUMME_BASISERTRAG], 8.93)
        self.assertEqual(res[lib.tranche.BEW_SUMME_WERTSTEIGERUNG], 710.00)
        self.assertEqual(res[lib.tranche.BEW_SUMME_AUSSCHUETTUNGEN], 15.19)
        self.assertEqual(res[lib.tranche.BEW_SUMME_WERT_ANFANG], 1810.00)
        self.assertEqual(res[lib.tranche.BEW_SUMME_WERT_ENDE], 2520.00)

class TestBeispielConfig(unittest.TestCase):
    def test_anderer_config(self):
        cfg = lib.config.Config("./config-beispiel.ini")
        self.assertEqual(cfg.all_sections(), ['databases', 'data', 'onvista', 'ariva', 'kursvergleiche'])
        self.assertEqual(cfg.get_filename_stammdaten(), "./beispiele/stammdaten.yaml")
        self.assertEqual(cfg.get_filename_depots(), "./beispiele/depots.yaml")
        self.assertEqual(cfg.get_filename_portfolio(), "./beispiele/portfolio.yaml")
        self.assertEqual(cfg.get_filename_ausschuettungen(), "./beispiele/ausschuettungen.yaml")
        self.assertEqual(cfg.get_filename_kursdatenbank(), "./beispiele/kurse_ov.db")

        stammdaten = lib.stammdaten.Stammdaten(cfg.get_filename_stammdaten())

        stammdaten.base_check()
        isinliste = stammdaten.get_all_isins()
        self.assertEqual(isinliste, ['LU1437016972', 'GB00BJDQQQ59', 'FR0010315770'])

        depots = lib.depot.Depot_Stammdaten(cfg.get_filename_depots())
        depots.base_check()

        transaktionen = lib.transaktionen.Transaktionen(cfg.get_filename_portfolio(), cfg.get_filename_ausschuettungen(), depots=depots, isinliste=isinliste)
        transaktionen.base_check()

        kursedb = lib.kursedb.KurseDB.open_sqlite(filename=":memory:", schema="sql/kurse.sql")
        kursedb.close()


if __name__ == '__main__':
    unittest.main()