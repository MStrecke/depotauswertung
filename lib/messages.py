#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Dieses Modul sammelt Nachrichten, damit sie am Ende (nochmals) gesammelt ausgegeben
# werden können.

class Messages:
    def __init__(self):
        self.errors = []
        self.warnings =  []
        self.infos = []

    @staticmethod
    def _add(liste:list, nachricht:str, printit:bool, printpre:str) -> None:
        if nachricht is not None:
            liste.append(nachricht)
            if printit:
                print(printpre+":", nachricht)

    def error(self, nachricht:str, printit:bool=True) -> None:
        self._add(self.errors, nachricht, printit, "Fehler")

    def info(self, nachricht:str, printit:bool=True) -> None:
        self._add(self.infos, nachricht, printit, "Info")

    def warning(self, nachricht:str, printit:bool=True) -> None:
        self._add(self.warnings, nachricht, printit, "Warnung")

    @staticmethod
    def _ausgabe(titel:str, liste:list, first:bool) -> bool:
        if liste == []:
            return first
        if not first:
            print()
            first = False
        print(titel)
        print("="*len(titel))
        for item in liste:
            print(item)

    def ausgabe(self, verbose=True) -> None:
        first = self._ausgabe("Fehler", self.errors, True)
        first = self._ausgabe("Warnungen", self.warnings, first)
        first = self._ausgabe("Infos", self.infos, first)

        if first and verbose:
            print("* Keine Meldungen")

    def has_errors(self) -> bool:
        return self.errors != []

# Zentraler Sammler
messages = Messages()