#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import importlib

module_list = None

# Zu berücksichtigende Pyhton-Dateien starten mit:
NAMESTART = "query_"

# Structure of MODULES_INFOS
#
# list of dicts items
#
# name                        name of the module (from Onlineabfrage.ID)
# mpoi                        module pointer

MODULES_INFOS = []

def get_modules_info():
    filelist = os.listdir(os.path.dirname(__file__))
    allmodlist = [x[:-3] for x in filelist if x.endswith(
        '.py') and x.startswith(NAMESTART)]

    active_mods = []
    for modname in allmodlist:
        # print("modname", modname)

        mpoi = importlib.import_module("." + modname, package=__name__)
        if not mpoi.SKIP_ME:
            minfo = {
                'name': mpoi.Onlineabfrage.ID,
                'module': mpoi
            }
            active_mods.append(minfo)
    return active_mods

# Zugriff auf bestimmte Abfrage
def get_abfrage_by_id(siteid):
    for mods in get_modules_info():
        if siteid != mods['name']:
            continue

        return mods
    return None

def iter_modules():
    for mod in MODULES_INFOS:
        yield mod

def init_abfragemodule(*, downloader, config, stammdaten):
    abfrager = []
    for qu in iter_modules():
        name = qu["name"]
        poi = qu["module"].Onlineabfrage(
            downloader= downloader,
            stammdaten=stammdaten,
            iniconfig=config)
        abfrager.append(
            { "name": name, "poi": poi}
        )
    return abfrager

MODULES_INFOS = get_modules_info()
