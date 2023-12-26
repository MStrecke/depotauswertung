#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import datetime
import json

# onvista_api_query = 'https://api.onvista.de/api/v1/instruments/FUND/{fund}/eod_history?idNotation={notation}&range=M1&startDate={startdate}'
# onvista_waehrung_query = 'https://api.onvista.de/api/v1/instruments/CURRENCY/USDEUR/eod_history?idNotation=1390618&range=M1&startDate=2023-10-07'
# https://api.onvista.de/api/v1/instruments
#   /FUND/{fund}
#   /CURRENCY/USDEUR
#   /eod_history?
#      idNotation={notation}&
#      range=M1&                     # 1 Monat (kostenfrei)
#      startDate={startdate}         # YYYY-MM-DD

ONVISTA_KURSE = "kurse"

class _OnvistaQuery:
    def __init__(self, *, downloader, stammdaten):
        self.downloader = downloader
        self.stammdaten = stammdaten

    def query_isin(self, *, isin:str, startdate:datetime.date):
        dat = self.stammdaten.get_entry(isin)
        assert dat is not None
        is_currency = dat.get("typ","").lower() == "currency"
        ov_fund = dat.get("onvista_entity")
        ov_notation = dat.get("onvista_notation")
        if ov_fund is None or ov_notation is None:
            raise ValueError("Onvista Fund or Notation not found for", isin)

        return self.query(
            fondid=ov_fund,
            notation=ov_notation,
            startdate=startdate,
            is_currency=is_currency
        )

    def query(self, *, fondid:str, notation:str, startdate:datetime.date, is_currency:bool=False):
        global stammdaten
        res = {}

        inst = "FUND"
        if is_currency:
            inst = "CURRENCY"

        start_str = startdate.strftime("%Y-%m-%d")

        query = f'https://api.onvista.de/api/v1/instruments/{inst}/{fondid}/eod_history?idNotation={notation}&range=M1&startDate={start_str}'

        status, data, rr = self.downloader.get_url(query)
        if status // 100 != 2:
            print("Fehler beim Zugriff", status)
            return None

        dj = json.loads(data)

        res["kvg"] = dj["market"]["name"]
        res["currency"] = dj["isoCurrency"]

        kurse =  []
        for item in zip(dj["datetimeLast"], dj["last"], dj["low"], dj["high"], dj["volume"]):
            kurse.append(
                {
                    "datum": datetime.datetime.utcfromtimestamp(item[0]),
                    "last": item[1],
                    "low": item[2],
                    "high": item[3],
                    "volume": item[4]
                }
            )
        res[ONVISTA_KURSE] = kurse
        return res
