#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import datetime

# Name der Dict-Elemente
KURSABFRAGE_DATUM = "datum"   # Datum des Kurses (datetime.datetime)
KURSABFRAGE_LAST = "last"     # Schlusskurs (float)

SKIP_ME = False               # auf True setzen, wenn abgeleitetes Modul nicht mehr verwendet werden soll

class FehlendeISINAbfrageParameterException(Exception):
    "Keine Parameter zur Abfrage einer ISIN in den Stammdaten"
    pass

class PlausibilitaetskontrolleException(Exception):
    "Plausibilitätskontrolle fehlgeschlagen"
    pass

class BaseOnlineabfrage:
    ID = None           # eindeutige ID - muss implementiert werden

    def __init__(self, *, downloader, stammdaten, iniconfig):
        self.downloader = downloader   # Web-Zugriff
        self.stammdaten = stammdaten   # Alle Fondsdaten => ID des Fonds für die API
        self.iniconfig = iniconfig     # => Zugangsdaten

    # Die Kursabfrage gibt nur die Kurse zurück.
    # Die `query_isin` muss aber auch eine Plausibilitätsprüfung durchführen:
    # - falls die Onlinedaten eine Währung bzw. einen Markt beinhalten, MUSS diese mit den
    #   Stammdaten verglichen und ggf. eine Exception geworfen werden.
    def query_isin(self, *, isin:str, startdate:datetime.date):
        raise NotImplementedError