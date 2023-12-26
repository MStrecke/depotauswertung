#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re
import datetime

from ..stammdaten import *
from ..kursedb import *
from ..utils import k2p, dstr, p2k
from lib.messages import messages

# Schlüssel im INI, das auf das CSV-Verzeichnis zeigt
CSV_KEY = "csv_verzeichnis"
FERTIG_SUBDIR = "fertig"

class DateinameEntsprichtNichtAnforderungError(ValueError): pass
class NeuerFondsAberKeineFreigabeZumAnlegenError(ValueError): pass
class ErsteZeileStimmtNichtError(ValueError): pass
class CSVZeileStimmtNichtError(ValueError): pass
class AnschlussNichtMoeglichError(ValueError): pass
class AnschlussdatumNichtGefundenError(ValueError): pass
class WaehrungStimmtNichtMitKurswaehrungUebereinError(ValueError): pass

class CsvReader:
    def __init__(self, *, stammdaten, kursedb, only_newer_entries=True, create_new_fonds=False, verbose=False) -> None:
        self.stammdaten = stammdaten
        self.kursedb = kursedb
        self.create_new_fonds = create_new_fonds
        self.only_newer_entries = only_newer_entries
        self.verbose = verbose

    def scan_dir(self, *, csv_dir:str, ignore_betrag:float=0.0, verschiebe_fertig:bool=True) -> None:
        """ Lese CSV-Dateien im angegebenen Verzeichnis ein

        :param csv_dir: Pfad mit den CSV-Dateien
        :type csv_dir: str
        :param ignore_betrag: erlaubte Abweichung beim Anschluss der Daten, defaults to 0.0
        :type ignore_betrag: float, optional
        :param verschiebe_fertig: verschiebe eingelesene Datei ins Unterverzeichnis 'fertig', defaults to True
        :type verschiebe_fertig: bool, optional
        :raises NeuerFondsAberKeineFreigabeZumAnlegenError: Neuer Fond gefunden, darf ihn aber nicht anlegen
        :raises AnschlussNichtMoeglichError: Anschluss nicht möglich
        :raises AnschlussdatumNichtGefundenError: Anschlussdatum nicht gefunden
        """
        # Dateien einlesen
        if self.verbose:
            print("* Scanne Verzeichnis:", csv_dir)

        with self.kursedb.cursor2() as kdb_cursor:
            for item in os.scandir(csv_dir):
                if item.is_file():
                    # nur .csv-Dateien
                    if not item.name.lower().endswith(".csv"):
                        continue

                    try:
                        isin, csv_daten = self.lese_csv(item)

                        isin_entry = self.stammdaten.get_entry(isin)
                        assert isin_entry is not None       # darf nicht vorkommen

                        isin_name = isin_entry[STAMMDATEN_NAME]
                        fondswaehrung = isin_entry[STAMMDATEN_KURSWAEHRUNG]

                        if self.verbose:
                            print("* gefundene ISIN %s: %s" % (isin, isin_name))

                        # Suche ISIN in db
                        kursindex = self.kursedb.isin2index(isin, cursor=kdb_cursor)
                        if kursindex is None:
                            if not self.create_new_fonds:
                                raise NeuerFondsAberKeineFreigabeZumAnlegenError(isin)
                            # neuen Fonds anlegen
                            kursindex = self.kursedb.insert_isin(isin, waehrung=fondswaehrung, cursor=kdb_cursor)

                        last_kurs = self.kursedb.get_last_kurs(kursindex, cursor=kdb_cursor)
                        if last_kurs is None:
                            if self.verbose:
                                print("* Keine Einträge in Kursdatenbank vorhanden")
                            last_datum = None
                        else:
                            last_datum = last_kurs[KURSEDB_DATUM]

                        # bestimme, welche Daten gespeichert werden sollen
                        zu_speichern = []
                        anschlussdatum_gefunden = False
                        for csvitem in csv_daten:

                            # Noch nichts in der Datenbank?
                            # `only_newer_entries` wird dabei ignoriert
                            if last_kurs is None:
                                anschlussdatum_gefunden = True
                                zu_speichern.append(csvitem)
                                continue

                            datum = csvitem[KURSEDB_DATUM]
                            if datum == last_datum:
                                anschlussdatum_gefunden = True
                                diff = abs(last_kurs[KURSEDB_SCHLUSSKURS] - csvitem[KURSEDB_SCHLUSSKURS])
                                if ignore_betrag is None:
                                    if diff > 0:
                                        raise AnschlussNichtMoeglichError(p2k(diff))
                                else:
                                    if diff > ignore_betrag:
                                        raise AnschlussNichtMoeglichError(p2k(diff))

                            if self.only_newer_entries:
                                # überspringe ältere Einträge
                                if datum > last_datum:
                                    zu_speichern.append(csvitem)
                                else:
                                    if self.verbose:
                                        print("* Überspringe Eintrag vom %s, da zu alt" % (dstr(datum), ))
                                continue

                        if not anschlussdatum_gefunden:
                            raise AnschlussdatumNichtGefundenError(dstr(last_datum))

                        # Alles ok bis hier
                        # Kurse speichern
                        self.kursedb.insert_kurse(isin, datalist=zu_speichern, cursor=kdb_cursor)

                        if verschiebe_fertig:
                            # Datei verschieben
                            unterverzeichnis_fertig = os.path.join(csv_dir, FERTIG_SUBDIR)
                            os.makedirs(unterverzeichnis_fertig, exist_ok=True)
                            neuer_name = os.path.join(unterverzeichnis_fertig, item.name)
                            if not os.path.exists(neuer_name):
                                if self.verbose:
                                    print("* %s -> %s" % (item.path, neuer_name))
                                os.rename(item.path, neuer_name)
                            else:
                                print("* %s exisitert bereits - wird nicht verschoben" % neuer_name)

                    except DateinameEntsprichtNichtAnforderungError:
                        messages.error("Dateiname entspricht nicht den Anforderungen: %s" % item.name)
                    except NeuerFondsAberKeineFreigabeZumAnlegenError as msg:
                        messages.warning("Neue ISIN, aber keine Freigabe zum Anlegen: %s" % msg)
                    except ErsteZeileStimmtNichtError as msg:
                        messages.error("Erste Zeile der CSV-Datei %s nicht entsprechend der Vorgabe:\n%s" % (
                            item.name,
                            msg
                        ))
                    except CSVZeileStimmtNichtError as msg:
                        messages.error("Aufbau einer CSV-Zeile in %s nicht entsprechend Vorgabe:\n%s" % (
                            item.name,
                            msg
                        ))
                    except WaehrungStimmtNichtMitKurswaehrungUebereinError as msg:
                        messages.error("Kurswährung stimmt nicht mit Währung in CSV überein: %s" % msg)
                    except AnschlussNichtMoeglichError as msg:
                        messages.error("Anschluss an die Kursdatenbank nicht möglich. Differenz: %s" % msg)
                    except AnschlussdatumNichtGefundenError as msg:
                        messages.error("Anschlussdatum nicht gefunden: %s" % msg)
                    except ValueError as msg:
                        messages.error("Wertefehler: %s" % msg)

class ArivaCsvReader(CsvReader):
    # Aufbau des Dateinamens
    # ([-_]+) ist die `wkn` aus der die ISIN hergeleitet wird
    ARIVA_CSV_NAME_CO = re.compile("^wkn_([-_])_historic.csv$")
    # 28.10.2021;87,669;87,669;87,669;87,669;EUR;0
    #                          BOM 1 2 3    4       5     6    7      8        9
    ARIVA_CSV_FIRSTLINE = "Datum;Erster;Hoch;Tief;Schlusskurs;Stuecke;Volumen"
    # 2023-11-30;99,3642;99,3642;99,3642;99,3642;;
    #   1   2  3    4       5        6      7   89
    #                                   1        2       3          4          5           6          7          8          9
    ARIVA_CSV_LINE_CO = re.compile("^(\d{4})-(\d{1,2})-(\d{1,2});([.,0-9]+);([.,0-9]+);([.,0-9]+);([.,0-9]+);([.,0-9]*);([.,0-9]*)$")

    def __init__(self, *, stammdaten, kursedb, create_new_fonds=False, verbose=False) -> None:
        super().__init__(
            stammdaten=stammdaten,
            kursedb=kursedb,
            create_new_fonds=create_new_fonds,
            verbose=verbose)

        # Stammdaten durchsuchen
        # Zuordnung `wkn` => `isin`
        self.wkn2isin = {}
        for item in stammdaten.iter_entries():
            notation = item.get(STAMMDATEN_WKN)
            if notation is not None:
                self.wkn2isin[notation] = item[STAMMDATEN_ISIN]

    def lese_csv(self, scanitem):
        ma = self.ARIVA_CSV_NAME_CO.search(scanitem.name)
        if ma is None:
            raise DateinameEntsprichtNichtAnforderungError(scanitem.name)

        wkn = int(ma.group(1))
        isin = self.wkn2isin.get(wkn)
        if isin is None:
            raise ValueError("WKN %s in Stammdaten nicht gefunden" % wkn)
        isin_entry = self.stammdaten.get_entry(isin)
        assert isin_entry is not None

        kurswaehrung = isin_entry[STAMMDATEN_KURSWAEHRUNG]
        daten = []
        with open(scanitem.path, "r") as fin:
            firstline = True
            while True:
                line = fin.readline()
                if line == "":
                    break
                line = line.strip()
                if firstline:
                    if line != self.ARIVA_CSV_FIRSTLINE:
                        raise ErsteZeileStimmtNichtError(line)
                    firstline = False
                    continue

                # CSV-Zeile auswerten
                ma = self.ARIVA_CSV_LINE_CO.match(line)
                if ma is None:
                    raise CSVZeileStimmtNichtError("%s: %s" % (isin, line))

                # Daten ermitteln
                datum = datetime.date(year=int(ma.group(1)), month=int(ma.group(2)), day=int(ma.group(3)))
                schluss = k2p(ma.group(7))
                stueck = k2p(ma.group(8), empty_is_none=True)
                volumen = k2p(ma.group(9), empty_is_none=True)
                # Keine Fondswährung, die geprüft werden könnte

                dat = {
                    KURSEDB_DATUM: datum,
                    KURSEDB_SCHLUSSKURS: schluss,
                    KURSEDB_STUECK: stueck,
                    KURSEDB_VOLUMEN: volumen,
                    KURSEDB_KURSWAEHRUNG: kurswaehrung,
                }
                daten.append(dat)

        # Ariva-Daten sind absteigend sortiert
        daten.sort(key=lambda x: x[KURSEDB_DATUM])
        return isin, daten

class OnvistaCsvReader(CsvReader):
    # Aufbau des Dateinamens
    # (\d+) ist die `onvista_notation` aus der die ISIN hergeleitet wird
    ONVISTA_CSV_NAME_CO = re.compile("^history_(\d+)-")
    # 28.10.2021;87,669;87,669;87,669;87,669;EUR;0
    ONVISTA_CSV_LINE_CO = re.compile("^(\d{1,2})\.(\d{1,2})\.(\d{4});([.,0-9]+);([.,0-9]+);([.,0-9]+);([.,0-9]+);(\S+);(\d+)$")
    #                          BOM 1 2 3    4       5     6    7      8        9
    ONVISTA_CSV_FIRSTLINE = "\ufeffDatum;Eröffnung;Hoch;Tief;Schluss;Währung;Volumen"

    def __init__(self, *, stammdaten, kursedb, create_new_fonds=False, only_newer_entries=False, verbose=False) -> None:
        super().__init__(
            stammdaten=stammdaten,
            kursedb=kursedb,
            create_new_fonds=create_new_fonds,
            only_newer_entries=only_newer_entries,
            verbose=verbose)

        # Stammdaten durchsuchen
        # Zuordnung `onvista_notation` => `isin`
        self.notation2isin = {}
        for item in self.stammdaten.iter_entries():
            notation = item.get("onvista_notation")
            if notation is not None:
                self.notation2isin[notation] = item[STAMMDATEN_ISIN]

    def lese_csv(self, scanitem):
        ma = self.ONVISTA_CSV_NAME_CO.search(scanitem.name)
        if ma is None:
            raise DateinameEntsprichtNichtAnforderungError(scanitem.name)

        nota = int(ma.group(1))
        isin = self.notation2isin.get(nota)
        if isin is None:
            raise ValueError("Keine Onvista-Notation %s in Stammdaten gefunden" % nota)

        isin_entry = self.stammdaten.get_entry(isin)
        assert isin_entry is not None                 # darf nicht vorkommen

        kurswaehrung = isin_entry[STAMMDATEN_KURSWAEHRUNG]

        neue_kurs_daten = []
        with open(scanitem.path, "r") as fin:
            firstline = True
            while True:
                line = fin.readline()
                if line == "":
                    break
                line = line.strip()
                if firstline:
                    if line != self.ONVISTA_CSV_FIRSTLINE:
                        raise ErsteZeileStimmtNichtError(line)
                    firstline = False
                    continue

                # CSV-Zeile auswerten
                ma = self.ONVISTA_CSV_LINE_CO.match(line)
                if ma is None:
                    raise CSVZeileStimmtNichtError("%s: %s" % (isin, line))

                # Daten ermitteln
                datum = datetime.date(year=int(ma.group(3)), month=int(ma.group(2)), day=int(ma.group(1)))
                schluss = k2p(ma.group(7))
                waehrung = ma.group(8)
                volumen = k2p(ma.group(9))

                if waehrung != kurswaehrung:
                    raise WaehrungStimmtNichtMitKurswaehrungUebereinError("%s - DB/CSV: %s / %s" % (
                        dstr(datum),
                        waehrung,
                        kurswaehrung
                    ))

                dat = {
                    KURSEDB_DATUM: datum,
                    KURSEDB_SCHLUSSKURS: schluss,
                    KURSEDB_VOLUMEN: volumen,
                    KURSEDB_KURSWAEHRUNG: waehrung,
                }
                neue_kurs_daten.append(dat)

        return isin, neue_kurs_daten



# Zuordnung: INI-Abschnitt -> Einleseroutine
INI_SECTIONS_WITH_CSV = [
    ("onvista", OnvistaCsvReader),
    ("ariva", ArivaCsvReader),
]

def do_csv_einlesen(*, cfg, stammdaten, kursedb, create_new_fonds=False, only_newer_entries=False, ignore=0, verbose=True):
    # Suche in der INI-Datei alle Abschnitte durch, die in INI_SECTIONS_WITH_CSV
    # angegeben sind. Diese Abschnitte können den Schlüssel `csv_verzeichnis` enthalten,
    # der auf das Verzeichnis mit den CSV-Dateien zeigt.

    ini_sections = cfg.all_sections()
    for source, csvclass in INI_SECTIONS_WITH_CSV:
        if source in ini_sections:
            sub_keys = cfg.get_section(source).keys()
            if CSV_KEY in sub_keys:
                csv_dir = os.path.expanduser(cfg._get(source, CSV_KEY))

                # Prüfe, on das Verzeichnis existiert
                if not os.path.exists(csv_dir):
                    messages.warning("%s existiert nicht" % csv_dir)
                else:
                    csvr = csvclass(
                        stammdaten=stammdaten,
                        kursedb=kursedb,
                        only_newer_entries=only_newer_entries,
                        create_new_fonds=create_new_fonds,
                        verbose=verbose)
                    csvr.scan_dir(csv_dir, ignore)
