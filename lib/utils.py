#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import datetime

def dstr(d):
    if d is None:
        return "????"
    if type(d) not in [datetime.datetime, datetime.date]:
        return str(d)
    return d.strftime("%d.%m.%Y")

def dparse(s:str) -> datetime.date:
    return datetime.datetime.strptime(s, "%d.%m.%Y").date()

def my_sign(x):
    # >0 -> 1
    # =0 -> 0
    # <0 -> -1
    return (x > 0) - (x < 0)

_DFAKTOR = [1, 10, 100, 1000, 10000, 100000]
def myround(w, digits=2):
    assert digits in [0,1,2,3,4,5]

    f = 1.0
    if w < 0:
        f = -1.0
        w = -w

    return f * int(0.5000000001 + w*_DFAKTOR[digits]) / _DFAKTOR[digits]


def k2p(s, *, empty_is_none=False) -> float:
    if s is None:
        return None

    if type(s) is float:
        return s

    if empty_is_none and s=="":
        return None

    return float(str(s).replace(".","").replace(",","."))

def p2k(s, nachkomma=None, *, sign=False) -> str:
    """ punkt nach komma

    :param s: Wert
    :type s: str/int
    :return: auszugebender Wert
    :rtype: str
    """
    if s is None:
        return "-"
    si = my_sign(s)
    if nachkomma is not None:
        s = myround(s, nachkomma)
    s = str(s).replace(",","_").replace(".",",").replace("_",".")
    if sign:
        if si == 1:
            s = "+" + s
        elif si == -1:
            s = "-" + s

    if nachkomma is None:
        return s
    add = nachkomma - len(s) + s.find(",") + 1
    if add >= 0:
        s += "0" * add
    return s
