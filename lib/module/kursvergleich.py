#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import datetime
from lib.kursedb import *
from lib.stammdaten import *
from lib.config import Config
from lib.utils import dstr

import matplotlib.pyplot as plt
import numpy as np
import matplotlib.dates as mdates

BEWERTUNGSWAEHRUNG = "EUR"

def db_kursvergleich(isins, startdatum:str, kursedb, stammdaten, savesvg=True):
    # Anzahl der Felder
    anz_felder = len(isins) + 1
    anz_reihen = anz_felder // 3
    if anz_felder % 3 != 0:
        anz_reihen += 1

    fig, ax = plt.subplots(nrows=anz_reihen, ncols=3,
                         sharex=True, figsize=(18, 5.8 * anz_reihen))

    # Achsen n * m => einfache Liste
    axs = ax.flatten()
    proz_ax = axs[anz_felder-1]  # letztes Feld für Prozentanzeige

    enddatum = datetime.date.today()

    DFORM = "%d.%m.%Y"
    proz_ax.set_title("G/V in %%: %s - %s" % (startdatum.strftime(DFORM), enddatum.strftime(DFORM)))
    proz_ax.grid(True)

    for maxs in axs:
        maxs.xaxis.set_major_formatter(mdates.DateFormatter('%d. %b %y'))

        # Rotates and right-aligns the x labels so they don't crowd each other.
        for label in maxs.get_xticklabels(which='major'):
            label.set(rotation=45, horizontalalignment='right')
            label.set_visible(True)


    stammd = {}
    for isin in isins:
        stammd[isin] = stammdaten.get_entry(isin)
        assert stammd is not None, "Keine Stammdaten für " + isin

    COLORS = ["red", "blue", "green", "black", "grey", "pink"]

    ax_counter = -1
    for isin in isins:
        ax_counter += 1
        color = COLORS[ax_counter]



        kx = kursedb.get_alle_kurse(isin, start=startdatum, ende=enddatum)

        if kx is None:
            raise ValueError("Keine Daten für %s in Kursdatenbank" % isin)

        startkurs = kursedb.get_kurs_db(isin, startdatum, exact=False)[KURSEDB_SCHLUSSKURS]
        if stammd[isin][STAMMDATEN_KURSWAEHRUNG] in [BEWERTUNGSWAEHRUNG, "Pkt."]:
            # keine Umrechnung erforderlich
            proz_kurs = [(x[KURSEDB_SCHLUSSKURS]-startkurs)/startkurs*100.0 for x in kx]
        else:
            # mit Währungs-Tageskurs bewerten
            waehrungsfaktor = kursedb.get_waehrungs_faktor(stammd[isin][STAMMDATEN_KURSWAEHRUNG], BEWERTUNGSWAEHRUNG, startdatum)
            if waehrungsfaktor in [None, 0]:
                raise ValueError("ISIN %s: keine Währungsumrechnung gefunden für %s am %s" % (
                    isin,
                    stammd[isin][STAMMDATEN_KURSWAEHRUNG],
                    dstr(startdatum)
                ))
            startkurs = startkurs * waehrungsfaktor
            proz_kurs = []
            for x in kx:
                dat = x[KURSEDB_DATUM]
                waehrungsfaktor = kursedb.get_waehrungs_faktor(stammd[isin][STAMMDATEN_KURSWAEHRUNG], BEWERTUNGSWAEHRUNG, dat)
                if waehrungsfaktor in [None, 0]:
                    raise ValueError("ISIN %s: keine Währungsumrechnung gefunden für %s am %s" % (
                        isin,
                        stammd[isin][STAMMDATEN_KURSWAEHRUNG],
                        dstr(dat)
                    ))
                proz_kurs.append((x[KURSEDB_SCHLUSSKURS]*waehrungsfaktor-startkurs)/startkurs*100.0)

        datx = [np.datetime64(x["datum"]) for x in kx]
        daty = [x["schluss"] for x in kx]

        axs[ax_counter].set_title("%s\n%s (%s)" % (stammd[isin][STAMMDATEN_NAME], isin, stammd[isin][STAMMDATEN_KURSWAEHRUNG]))
        axs[ax_counter].title.set_size(10)
        axs[ax_counter].plot_date(datx, daty, fmt=color, linestyle="solid", xdate=True, ydate=False)

        proz_ax.plot_date(datx, proz_kurs, fmt=color, linestyle="solid", xdate=True, ydate=False)

    # Größe anpassen (schräggestellte X-Werte)
    fig.autofmt_xdate()

    if savesvg:
        isinfnm = "_".join(isins)
        fnm = "/tmp/%s_%s_%s.svg" % (isinfnm, startdatum.strftime("%Y%m%d"), enddatum.strftime("%Y%m%d"))
        print("Gespeichert in " + fnm)
        plt.savefig(fnm, format='svg', bbox_inches='tight')
    plt.show()

