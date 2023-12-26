#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from lib.isincheck import isin_check

KURZLISTE = ["isin","name", "thesaurierend", "teilfreistellung", "ter", "anmerkung"]

def stammdaten_anzeigen(stammdaten, isinliste, kurz=False):

    first = True
    for isin in isinliste:
        if not first:
            print("===========================")
        if not isin_check.check(isin):
            print("ISIN fehlerhaft")
            continue
        res = stammdaten.get_entry(isin)
        if res is None:
            print("* Keine Stammdaten für gefunden %s gefunden" % isin)
        else:
            if kurz:
                for item in KURZLISTE:
                    w = res.get(item)
                    if w is not None:
                        print("%s: %s" % (item, w))
            else:
                for key in res.keys():
                    print("%s: %s" % (key, res[key]))
        first = False

