#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import configparser
import re
import os

CONF_SECTION_DATA = "data"
CONF_SECTION_DATABASES = "databases"
CONF_SECTION_KURSVERGLEICHE = "kursvergleiche"

class Config:
    def __init__(self, filename:str):
        self.filename = filename
        self.cfg = configparser.ConfigParser()
        self.cfg.read([self.filename, ])

    def _get(self, section, key):
        if section not in self.cfg.sections():
            ValueError("Abschnitt %s fehlt in %s" % (section, self.filename))

        if key is not None:
            if key not in self.cfg[section]:
                ValueError("Schlüssel %s fehlt in Abschnitt %s in %s" % (key, section, self.filename))
            return self.cfg[section][key]
        else:
            return self.cfg[section].keys()

    def all_sections(self):
        return self.cfg.sections()

    def get_section(self, section):
        if section not in self.cfg.sections():
            return None
        return self.cfg[section]

    def get_filename_stammdaten(self):
        return os.path.expanduser(self._get(CONF_SECTION_DATA, "wertpapiere_stammdaten"))

    def get_filename_depots(self):
        return os.path.expanduser(self._get(CONF_SECTION_DATA, "depots"))

    def get_filename_portfolio(self):
        return os.path.expanduser(self._get(CONF_SECTION_DATA, "portfolio"))

    def get_filename_ausschuettungen(self):
        return os.path.expanduser(self._get(CONF_SECTION_DATA, "ausschuettung"))

    def get_filename_kursdatenbank(self):
        return os.path.expanduser(self._get(CONF_SECTION_DATABASES, "kurse"))

    def get_namen_kursvergleiche(self):
        if CONF_SECTION_KURSVERGLEICHE not in self.cfg.sections():
            return None
        return list(self.cfg[CONF_SECTION_KURSVERGLEICHE].keys())

    def get_gespeicherter_kursvergleich(self, name):
        if CONF_SECTION_KURSVERGLEICHE not in self.cfg.sections():
            return None
        dat = self.cfg[CONF_SECTION_KURSVERGLEICHE].get(name)
        if dat is None:
            return None

        dm = [x.strip() for x in dat.split(" ") if x.strip() != ""]
        datum = None
        isins = []
        for item in dm:
            if re.match("^\d{1,2}\.\d{1,2}\.\d{4}$", item):
                datum = item
            else:
                isins.append(item)

        res = {}
        if datum is not None:
            res["datum"] = datum
        res["isins"] = isins
        return res

