#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import datetime

import argparse

from lib.simpledownloader import SimpleDownloader
from lib.kursedb import *
from lib.stammdaten import *
from lib.depot import *
from lib.transaktionen import *
from lib.utils import *
from lib.isincheck import isin_check
from lib.config import Config
from lib.messages import messages

CONFIGFILE = "config.ini"

def isin_stammdaten_anzeigen(args):
    global stammdaten

    import lib.module.zeige_stammdaten

    assert isin_check.check_list(args.isins)

    lib.module.zeige_stammdaten.stammdaten_anzeigen(
        stammdaten,
        args.isins,
        kurz=args.kurz
    )

def alle_db_isins(args):
    global stammdaten
    global kursedb

    import lib.module.kursdatenbankinfo

    lib.module.kursdatenbankinfo.alle_db_isins(kursedb=kursedb, stammdaten=stammdaten)

def online_lookup(args):
    global dl, stammdaten, cfg

    import lib.module.kurse_online

    assert isin_check.check_list(args.isin)
    isin = args.isin

    abfragedatum = datetime.datetime.strptime(args.datum, "%d.%m.%Y").date()
    lib.module.kurse_online.online_kurs_lookup(
        downloader=dl,
        isin=isin,
        abfragedatum=abfragedatum,
        stammdaten=stammdaten,
        config=cfg)

def db_kursvergleich(args):
    import lib.module.kursvergleich
    global stammdaten, kursedb

    assert isin_check.check_list(args.isins)

    lib.module.kursvergleich.db_kursvergleich(
        args.isins,
        startdatum=datetime.datetime.strptime(args.startdatum, "%d.%m.%Y").date(),
        kursedb=kursedb,
        stammdaten=stammdaten,
        savesvg=args.savesvg
    )

def db_kursvergleiche_gespeichert(args):
    global cfg
    import lib.module.kursvergleich
    global stammdaten, kursedb

    params = cfg.get_gespeicherter_kursvergleich(args.name)
    # argparse stellt sicher, dass nur gespeicherte Keys angegeben werden.
    assert params is not None

    startdatum = args.startdatum
    if startdatum is None:
        startdatum = params.get("datum")
    if startdatum is None:
        raise ValueError("Kein Startdatum angegeben")

    isins = params.get("isins")
    if isins in [None, []]:
        raise ValueError("Keine ISINs angegeben")

    assert isin_check.check_list(isins)

    lib.module.kursvergleich.db_kursvergleich(
        isins,
        startdatum=datetime.datetime.strptime(startdatum, "%d.%m.%Y").date(),
        kursedb=kursedb,
        stammdaten=stammdaten,
        savesvg=args.savesvg
    )


def db_abfrage(args):
    global stammdaten
    global kursedb

    import lib.module.kursdatenbankinfo

    isin = args.isin
    assert isin_check.check_list(args.isin)

    abfragedatum = datetime.datetime.strptime(args.datum, "%d.%m.%Y").date()

    lib.module.kursdatenbankinfo.kursabfrage(
        isin=isin,
        datum=abfragedatum,
        kursedb=kursedb,
        stammdaten=stammdaten
    )

def do_transaktionen(args):
    global transaktionen
    global stammdaten

    assert isin_check.check_list(args.isins)

    import lib.module.zeige_transaktionen
    lib.module.zeige_transaktionen.zeige_transaktionen.zeige_transaktionen(
        transaktionen=transaktionen,
        stammdaten=stammdaten,
        isin=args.isin,
        depot=args.depot
    )


def do_refresh(args):
    global kursedb
    global dl
    global stammdaten

    import lib.module.kurse_online

    try:
        lib.module.kurse_online.refresh_datenbank(
            downloader=dl,
            kursedb=kursedb,
            stammdaten=stammdaten,
            config=cfg,
            ignore=k2p(args.ignore),
            verbose=args.verbose
        )
    except ValueError as msg:
        messages.error(msg)

def do_vorabpauschale_jahr(args):
    global kursedb
    global stammdaten
    global transaktionen

    import lib.module.vorabpauschale

    lib.module.vorabpauschale.do_vorabpauschale_jahr(
        isin=args.isin,
        jahr=args.jahr,
        depot=args.depot,
        kursedb=kursedb,
        transaktionen=transaktionen,
        stammdaten=stammdaten
    )

def do_csv(args):
    import lib.module.csv_einlesen

    global cfg
    global stammdaten
    global kursedb

    lib.module.csv_einlesen.do_csv_einlesen(
        cfg=cfg,
        stammdaten=stammdaten,
        kursedb=kursedb,
        create_new_fonds=args.neue,
        only_newer_entries=False,      # not args.alte,
        ignore=k2p(args.ignore),
        verbose=True
    )

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Depotauswertung')

    try:
        # Konfiguration
        cfg = Config(CONFIGFILE)

        # Ein Downloader für "Refresh"
        dl = SimpleDownloader()

        # Wertpapier-Stammdaten
        stammdaten = Stammdaten(cfg.get_filename_stammdaten())
        stammdaten.base_check()

        # Prüfsummen-Check
        # bei Dummy-ISINs überspringen
        isinliste = stammdaten.get_all_isins()
        for isin in isinliste:
            entry = stammdaten.get_entry(isin)
            if entry[STAMMDATEN_TYP].lower() in [STAMMDATEN_TYP_CURRENCY, STAMMDATEN_TYP_INDEX]:
                isin_check.set_skip_check_for(isin)

        # Depots
        depots = Depot_Stammdaten(cfg.get_filename_depots())
        depots.base_check()

        # Transaktionen (Käufe, Verkäufe, Ausschüttungen)
        transaktionen = Transaktionen(cfg.get_filename_portfolio(), cfg.get_filename_ausschuettungen(), depots=depots, isinliste=isinliste)
        transaktionen.base_check()

        # Kursdatenbank
        kursedb = KurseDB.open_sqlite(filename=cfg.get_filename_kursdatenbank(), schema="sql/kurse.sql")

        # Namen der gespeicherten Kursvergleiche für argparse
        gespeicherte_kursvergleiche = cfg.get_namen_kursvergleiche()
    except FileNotFoundError as msg:
        print("*** Datei/Verzeichnis nicht gefunden:", msg.filename)
        parser.exit(101)
    except ValueError as msg:
        print("**** Wertefehler:", msg)
        parser.exit(102)


    parser.add_argument('--verbose', '-v',
        action='store_true',
        default=False,
        help='mehr Ausgaben')

    subparsers = parser.add_subparsers(title='Unterbefehle',
                                    description='gültige Unterbefehle',
                                    help='zusätzliche Hilfe')

    parser_a = subparsers.add_parser('stammdaten', help='zeige Stammdaten zu ISIN')
    parser_a.add_argument('--kurz', '--short', action="store_true", help='nur bestimmte Keys zeigen')
    parser_a.add_argument('isins', type=str, nargs="+", help='ISIN-Nummer(n)')
    parser_a.set_defaults(func=isin_stammdaten_anzeigen)

    parser_a = subparsers.add_parser('transaktionen', help='Transaktionen anzeigen')
    parser_a.add_argument('isin', type=str, help='ISIN-Nummer')
    parser_a.add_argument('depot', type=str, nargs="?", help='optional: Depot')
    parser_a.set_defaults(func=do_transaktionen)

    parser_a = subparsers.add_parser('db_isins', help='zeige ISINs in Kursdatenbank')
    parser_a.set_defaults(func=alle_db_isins)

    parser_a = subparsers.add_parser('db_kurs', help='Kursabfrage in offline Datenbank')
    parser_a.add_argument('isin', type=str, help='ISIN-Nummer')
    parser_a.add_argument('datum', type=str, help='TT.MM.JJJJ')
    parser_a.set_defaults(func=db_abfrage)

    parser_a = subparsers.add_parser('kursvergleich', help='Offline-Kursplot zweier oder mehrerer ISINs')
    parser_a.add_argument('--savesvg', action="store_true", help="Grafik in /tmp speichern")
    parser_a.add_argument('startdatum', type=str, help='TT.MM.JJJJ')
    parser_a.add_argument('isins', type=str, nargs="+", help='ISIN-Nummern')
    parser_a.set_defaults(func=db_kursvergleich)

    parser_a = subparsers.add_parser('kv', help='Offline-Kursplot mit vordefinierten Abfragen')
    parser_a.add_argument('--savesvg', action="store_true", help="Grafik in /tmp speichern")
    parser_a.add_argument('name', type=str, choices=gespeicherte_kursvergleiche, help='Name der KV-Konfiguration')
    parser_a.add_argument('startdatum', type=str, nargs="?", help='TT.MM.JJJJ')
    parser_a.set_defaults(func=db_kursvergleiche_gespeichert)

    parser_a = subparsers.add_parser('csv', help='Kurse aus CSV-Dateien einlesen')
    parser_a.add_argument('--neue', action="store_true", help='Anlegen neuer Fonds ermöglichen')
    # parser_a.add_argument('--alte', action="store_true", help='Anlegen von Einträgen vor neustem Eintrag ermöglichen')
    parser_a.add_argument('--ignore', type=str, help='Ignoriere Unstimmigkeiten beim Anschluss (abs.)')
    parser_a.set_defaults(func=do_csv)

    parser_a = subparsers.add_parser('refresh', help='neue Kurse holen')
    parser_a.add_argument('--ignore', type=str, help='Ignoriere Unstimmigkeiten beim Anschluss (abs.)')
    parser_a.set_defaults(func=do_refresh)

    parser_a = subparsers.add_parser('vorab', help='Alle Vorabpauschalen berechnen')
    parser_a.add_argument('jahr', type=int, help='Jahr')
    parser_a.add_argument('--isin', type=str, help='eingrenzen auf ISIN')
    parser_a.add_argument('--depot', type=str, help='eingrenzen auf Depot')
    parser_a.set_defaults(func=do_vorabpauschale_jahr)

    parser_a = subparsers.add_parser('online_lookup', help='Online-Kursabfrage')
    parser_a.add_argument('isin', type=str, help='ISIN-Nummer')
    parser_a.add_argument('datum', type=str, help='TT.MM.JJJJ')
    parser_a.set_defaults(func=online_lookup)

    args = parser.parse_args()
    func = getattr(args, "func", None)
    if func is not None:
        try:
            args.func(args)
        except AssertionError as msg:
            messages.error(msg)
        except ValueError as msg:
            messages.error(msg)
    else:
        parser.print_help()

    messages.ausgabe(verbose=False)
    if messages.has_errors():
        parser.exit(1)
    parser.exit(0)                    # = sys.exit(0)
