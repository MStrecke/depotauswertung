#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from lib.transaktionen import *
from lib.stammdaten import *
from lib.config import Config
from lib.utils import p2k, k2p

def zeige_transaktionen(*, transaktionen, stammdaten, isin, depot):
    print("ISIN :", isin)
    print("Depot:", depot)
    entry = stammdaten.get_entry(isin)
    assert entry is not None, "Keine Stammdaten für "+isin
    print("Name :", entry[STAMMDATEN_NAME])
    res = transaktionen.get_by_isin(isin, depot=depot)
    if len(res) == 0:
        print("* Keine Einträge")
        return

    print("\nDatum      Depot      Typ            Betrag     Anzahl       Kurs")
    for item in res:
        print("%10s %-10s %-10s" %
              (
                item[TRANSAKTION_DATUM],
                item[TRANSAKTION_DEPOT],
                item[TRANSAKTION_TYP]
              ), end=" ")

        if item[TRANSAKTION_TYP] == TRANSAKTION_AUSSCHUETTUNG:
            print("%7s" % p2k(k2p(item.get(AUSSCHUETTUNG_BETRAG)),2))
        else:
            print("%21s %10s" % (
                p2k(k2p(item.get(TRANSAKTION_ANZAHL)),4),
                p2k(k2p(item.get(TRANSAKTION_KURS)),4)
              ))
