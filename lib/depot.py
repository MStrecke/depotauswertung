#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import yaml
from .yamlbase import YamlBase

DEPOT_ID = "name"
DEPOT_WAEHRUNG = "waehrung"

class Depot_Stammdaten(YamlBase):
    def __init__(self, filename):
        YamlBase.__init__(self, filename, [DEPOT_ID, DEPOT_WAEHRUNG])

        self.waehrungscache = {}
        for item in self.iter_entries():
            dpw = item.get(DEPOT_WAEHRUNG)
            if dpw is None:
                raise ValueError("Dem Depot %s fehlt der Eintrag `waehrung`" % item[DEPOT_ID])
            self.waehrungscache[item[DEPOT_ID]] = dpw

    def get_depotwaehrung(self, depotid):
        if depotid is None:
            return None
        return self.waehrungscache[depotid]

    def get_entry(self, depotid):
        for item in yaml.load_all(open(self.filename, "r", encoding="utf8"), Loader=yaml.SafeLoader):
            if item[DEPOT_ID] == depotid:
                return item
        return None

    def base_check(self):
        super().base_check()
        for item in self.iter_entries():
            self.content_not_empty(item, DEPOT_ID, info=None)

    def get_alle_depots(self):
        """ Erzeuge eine Liste aller Depot-IDs

        :return: Depot-IDs
        :rtype: list(str)
        :note: Es wird darauf geachtet, dass die ID nicht mehrfach vorkommt.
        """
        res = []
        for item in self.iter_entries():
            depotid = item[DEPOT_ID]
            assert depotid not in res, "Depot-ID mehrfach vergeben: "+depotid
            res.append(depotid)
        return res
