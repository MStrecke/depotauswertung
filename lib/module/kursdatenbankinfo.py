#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from lib.stammdaten import *
from lib.kursedb import *
from lib.utils import dstr, p2k

def alle_db_isins(*, kursedb, stammdaten):

    print("ISIN   Verwend. Währ. # Daten  erster Kurs letzter   Name\n")
    with kursedb.cursor2() as cursor:
        for isin in kursedb.all_isins(cursor=cursor):
            dat = stammdaten.get_entry(isin)
            assert dat is not None, "Keine Stammdaten für " + isin

            anz_kurse = kursedb.count_kurse(isin=isin, cursor=cursor)
            first, last = kursedb.erster_letzter_kurs(isin=isin, cursor=cursor)
            if first is None:
                fday = "--.--.----"
            else:
                fday = dstr(first[KURSEDB_DATUM])

            if last is None:
                lday = "--.--.----"
            else:
                lday = dstr(last[KURSEDB_DATUM])

            print("%-13s %s %s  %7s  %s %s  %s" % (
                isin,
                theausierend_mark(dat, " "),
                dat[STAMMDATEN_KURSWAEHRUNG],
                anz_kurse,
                fday,
                lday,
                dat[STAMMDATEN_NAME]
            ))

def kursabfrage(*, isin, datum, kursedb, stammdaten):
    stammd = stammdaten.get_entry(isin)
    print(stammd[STAMMDATEN_NAME])
    print()
    res = kursedb.get_kurs(isin, datum)
    if res[KURSEDB_EXAKTES_DATUM]:
        print("* exaktes Datum")
    else:
        print("* Kurs von früherem Datum:", dstr(res[KURSEDB_DATUM]))
    print(dstr(res[KURSEDB_DATUM]), p2k(res[KURSEDB_SCHLUSSKURS]), res[KURSEDB_KURSWAEHRUNG])
