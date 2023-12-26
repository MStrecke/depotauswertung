#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from .yamlbase import YamlBase
from lib.isincheck import isin_check
import re

STAMMDATEN_ISIN = "isin"
STAMMDATEN_NAME = "name"
STAMMDATEN_KURSWAEHRUNG = "kurswaehrung"
STAMMDATEN_TEILFREISTELLUNG = "teilfreistellung"
STAMMDATEN_TYP = "typ"
STAMMDATEN_TYP_CURRENCY = "currency"       # Kleinschreibung
STAMMDATEN_TYP_INDEX = "index"             # Kleinschreibung
STAMMDATEN_TYP_FUND = "fund"
STAMMDATEN_THESAURIEREND = "thesaurierend"
STAMMDATEN_WKN = "wkn"

def theausierend_mark(entry, nonestr="?"):
    t = entry.get(STAMMDATEN_THESAURIEREND)
    if t is None:
        return nonestr
    if t:
        return "T"
    return "A"

TEILFREISTELLUNG_CO = re.compile("^\d+%$")

class Stammdaten(YamlBase):
    def __init__(self, filename):
        YamlBase.__init__(self, filename, [STAMMDATEN_ISIN, STAMMDATEN_NAME, STAMMDATEN_TEILFREISTELLUNG, STAMMDATEN_KURSWAEHRUNG, STAMMDATEN_TYP])

    def get_entry(self, isin):
        return self.stringsuche(STAMMDATEN_ISIN, isin)

    def get_all_isins(self):
        alle = []
        for item in self.iter_entries():
            if item[STAMMDATEN_ISIN] in alle:
                raise ValueError("Doppelte ISIN in Stammdaten " + item[STAMMDATEN_ISIN])
            alle.append(item[STAMMDATEN_ISIN])
        return alle


    def base_check(self):
        super().base_check()
        for item in self.iter_entries():
            isin = item[STAMMDATEN_ISIN]
            self.regex_check(item, STAMMDATEN_TEILFREISTELLUNG,TEILFREISTELLUNG_CO, info=isin)
            self.content_not_empty(item, STAMMDATEN_NAME, info=isin)
            self.content_not_empty(item, STAMMDATEN_KURSWAEHRUNG, info=isin)
            self.content_must_be(item, STAMMDATEN_TYP, ["etf", "fonds", "currency", "index"], info=isin, fkt=lambda x: x.lower())
            if item[STAMMDATEN_TYP].lower() not in ["currency", "index"]:
                assert isin_check.check_list(isin)

