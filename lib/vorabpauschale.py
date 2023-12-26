#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import datetime

BASISZINS_VH = {
    2018: 0.87,
    2019: 0.52,
    2020: 0.07,
    2021: 0.00,
    2022: 0.00,
    2023: 2.55,
}

def get_basiszins_proz(jahr):
    if jahr < 2018:
        return 0.0
    return BASISZINS_VH.get(jahr)

def monatsanteil(dat:datetime.date) -> float:
    # Abzug um 1/12 für jeden vollen Monat vor dem Datum
    return (13.0 - dat.month) / 12.0
