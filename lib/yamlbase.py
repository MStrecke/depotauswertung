#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import yaml

class YamlBase:
    def __init__(self, filename, mandatory_keys_list):
        self.filename = filename
        self.mandatory_keys = set(mandatory_keys_list)

    def iter_entries(self):
        with open(self.filename, "r", encoding="utf8") as fin:
            for item in yaml.load_all(fin, Loader=yaml.SafeLoader):
                yield item

    def check_mandatory_entries(self):
        for item in self.iter_entries():
            kl = self.mandatory_keys - set(item.keys())
            if kl != set():
                print("Folgender Eintrag in '%s' hat nicht alle erforderlichen Einträge" % self.filename)
                print(item)
                print("Es fehlen:", ", ".join(kl))
                raise ValueError("Nicht alle erforderlichen Einträge in %s vorhanden: %s" % (self.filename, ", ".join(kl)))

    def base_check(self):
        self.check_mandatory_entries()

    @staticmethod
    def regex_check(item, itemkey:str, compregex,*, default:bool=False, info=None) -> bool:
        if itemkey not in item:
            return default
        # Ganze Zahlen werden von Yaml als Int zurückgegeben
        res = compregex.search(str(item[itemkey]))
        if res is None:
            if info is None:
                info =""
            else:
                info = info + " "
            raise ValueError("%s Fehler: %s entspricht nicht den Vorgaben" % (info, itemkey))
        return True

    @staticmethod
    def content_not_empty(item, itemkey:str, info=None):
        if (itemkey not in item) or (item[itemkey] in [None, ""]):
            raise ValueError("%sFehler: %s ist leer" % (info, itemkey))

    @staticmethod
    def content_must_be(item, itemkey:str, validvalues, info=None, fkt=None):
        """ Prüfe, ob Eintrag den geforderten Stringwert hat

        :param item: Datensatz
        :type item: dict
        :param itemkey: Name des Eintrags
        :type itemkey: str
        :param validvalues: Liste der gültigen Einträge
        :type validvalues: list of str
        :param info: zusätzliche Info bei Fehler, defaults to None
        :type info: str, optional
        :param fkt: Konvertierroutine vor Vergleich, defaults to None
        :type fkt: function, optional
        :raises ValueError: Fehlermeldung
        """
        if fkt is None:
            fkt = lambda x: x
        if info is not None:
            info = info + " "
        if (itemkey not in item) or (fkt(item[itemkey]) not in validvalues):
            raise ValueError("%sFehler: %s ist '%s', nicht: %s" % (info, itemkey, item.get(itemkey), ", ".join(validvalues)))

    def stringsuche(self, keyname, suchstring):
        assert keyname in self.mandatory_keys

        for item in self.iter_entries():
            if item[keyname] == suchstring:
                return item

        return None
