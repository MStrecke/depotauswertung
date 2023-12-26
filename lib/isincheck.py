#!/usr/bin/env python3
# -*- coding: utf-8 -*-

class IsinCheck:
    # http://www.pruefziffernberechnung.de/I/ISIN.shtml

    def __init__(self):
        self.cache = []
        self.skip_check_for = set()

    def set_skip_check_for(self, isin):
        # z.B. Währungen und Indices
        self.skip_check_for.add(isin)

    def check(self, isin):
        if isin is None:
            return False

        if isin in self.skip_check_for:
            return True

        if len(isin) != 12:
            return False
        if isin in self.cache:
            return True

        # Wert der Prüfziffer (letztes Zeichen)
        pruefziffer = ord(isin[-1]) - ord('0')
        calc_pruefziffer = self._calc_pruefziffer(isin[:-1])    # Ziffer oder None

        if pruefziffer == calc_pruefziffer:
            self.cache.append(isin)
            return True

        return False

    @staticmethod
    def _calc_pruefziffer(isinrest):
        if isinrest is None:
            return False
        if len(isinrest) != 11:
            return False

        isinrest = isinrest.upper()

        # Erste Transformation
        # Buchstaben -> Zahlen
        isin_d = ""
        for c in isinrest:
            if c in '0123456789':
                isin_d += c
            elif c in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ':
                isin_d += str(ord(c) - ord('A') + 10)
            else:
                return None                   # unbekanntes Zeichen

        # Zahlen-ISIN (ohne Prüfziffer) von hinten abwechselnd mit 2 und 1 multiplizieren
        # Die Quersumme der Produkte aufsummieren
        # Prüfziffer = ((10 - Summe % 10) % 10)

        summe = 0
        pos = 0   # Position von hinten
        for i in range(len(isin_d)-1,-1, -1):  # len-1 ... 0
            if pos % 2 == 0:  # gerade: 0, 2, 4, ...
                gewichtung = 2
            else:
                gewichtung = 1
            pos += 1

            wert = ord(isin_d[i]) - ord('0')
            produkt = wert * gewichtung

            # 0 <= Produkt <= 70
            summe += ((produkt // 10) + (produkt % 10))

        return (10 - (summe % 10)) % 10

    def check_list(self, isins,*, verbose:bool=True) -> bool:
        """ Einzelne oder mehrere ISINs überprüfen (Prüfziffer) mit Ausgabe fehlerhafer ISINs

        :param isins: ISIN(s)
        :type isins: str oder list von str
        :param verbose: Ausgabe fehlerhafter ISINs
        :type bool: bool, default=True
        :return: alles ok
        :rtype: bool
        """
        if isins is None:
            return True

        if type(isins) == str:
            isins = [isins]

        alles_ok = True
        for isin in isins:
            if not self.check(isin):
                alles_ok = False
                if verbose:
                    print("* Fehlerhafte ISIN: " + isin)

        return alles_ok

isin_check = IsinCheck()

