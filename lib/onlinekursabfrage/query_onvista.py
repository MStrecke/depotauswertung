#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from .base import *
from ..stammdaten import STAMMDATEN_TYP, STAMMDATEN_TYP_CURRENCY, STAMMDATEN_KURSWAEHRUNG, STAMMDATEN_TYP_FUND, STAMMDATEN_TYP_INDEX
from lib.messages import messages

import json

SKIP_ME = False

# Keys in Stammdaten für Onvista
ONVISTA_ENTITY = "onvista_entity"
ONVISTA_NOTATION = "onvista_notation"
class Onlineabfrage(BaseOnlineabfrage):
    ID = "onvista"

    def query_isin(self, *, isin:str, startdate:datetime.date):
        dat = self.stammdaten.get_entry(isin)
        assert dat is not None, "Keine Stammdaten für " + isin

        entitytype = dat.get(STAMMDATEN_TYP,"")
        fondswaehrung = dat.get(STAMMDATEN_KURSWAEHRUNG)

        ov_fund = dat.get(ONVISTA_ENTITY)
        ov_notation = dat.get(ONVISTA_NOTATION)
        if ov_fund is None or ov_notation is None:
            raise FehlendeISINAbfrageParameterException("Onvista Fund oder Notation nicht gefunden für " + isin)

        return self._query(
            fondid=ov_fund,
            notation=ov_notation,
            startdate=startdate,
            fondswaehrung=fondswaehrung,
            entitytype=entitytype
        )

    def _query(self, *, fondid:str, notation:str, startdate:datetime.date, fondswaehrung:str, entitytype=None):
        global stammdaten

        etyp = entitytype.lower()

        inst = "FUND"
        check_currency = True
        check_kvg = True

        if etyp == STAMMDATEN_TYP_CURRENCY:
            inst = "CURRENCY"
            check_currency = False
            check_kvg = False
        elif etyp == STAMMDATEN_TYP_INDEX:
            inst = "INDEX"
            check_kvg = False

        start_str = startdate.strftime("%Y-%m-%d")
        query = f'https://api.onvista.de/api/v1/instruments/{inst}/{fondid}/eod_history?idNotation={notation}&range=M1&startDate={start_str}&withEarnings=false'

        status, data, _ = self.downloader.get_url(query)
        if status // 100 != 2:
            messages.warning("Onvista, Webzugriff, Fehler %s" % status)
            return None

        dj = json.loads(data)

        if check_kvg:
            if dj["market"]["name"] != "KVG":
                raise PlausibilitaetskontrolleException("Onvista: Markt nicht KVG")

        if not check_currency and (dj["isoCurrency"] != fondswaehrung):
            raise PlausibilitaetskontrolleException("Onvista: Fondswährung %s für %s weicht von Stammdaten ab: %s" % (
                dj["isoCurrency"], fondid, fondswaehrung
            ))

        kurse = []
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
        return kurse
