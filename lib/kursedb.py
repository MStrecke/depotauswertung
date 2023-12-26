#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from lib.sqlite import DBClass, local_cursor_wrapper
import datetime

KURSEDB_ISIN = "isin"
KURSEDB_FONDID = "fondsid"
KURSEDB_KURSWAEHRUNG = "waehrung"
KURSEDB_DATUM = "datum"
KURSEDB_SCHLUSSKURS = "schluss"
KURSEDB_VOLUMEN = "volumen"
KURSEDB_STUECK = "stück"

KURSEDB_EXAKTES_DATUM = "exakt"    # bei Kursabfrage

class KurseDB(DBClass):
    @local_cursor_wrapper
    def all_isins(self, cursor=None):
        return [x[KURSEDB_ISIN] for x in self.fetchall("SELECT isin FROM fonds ORDER BY isin", None)]

    @local_cursor_wrapper
    def isin2index(self, isin, cursor=None):
        return self.fetchone("SELECT fondsid FROM fonds WHERE isin=?", (isin,), singleparam="fondsid", cursor=cursor)

    @local_cursor_wrapper
    def count_kurse(self, *, isin=None, cursor=None):
        if isin is None:
            return self.fetchone("SELECT count(*) FROM kurse", None, singleparam="count(*)", cursor=cursor)
        ix = self.isin2index(isin)
        if ix is None:
            return None

        return self.fetchone("SELECT count(*) FROM kurse WHERE fondsid=?", (ix,), singleparam="count(*)", cursor=cursor)

    @local_cursor_wrapper
    def erster_letzter_kurs(self, *, isin=None, cursor=None):
        if isin is None:
            return None, None
        ix = self.isin2index(isin)
        if ix is None:
            return None, None

        res = self.fetchone("SELECT min(datum), max(datum) FROM kurse WHERE fondsid=?", (ix,), cursor=cursor)
        if res is None:
            return None, None

        erste = self.fetchone("SELECT * FROM kurse WHERE datum=? and fondsid=?", (res["min(datum)"], ix), cursor=cursor)
        letzte = self.fetchone("SELECT * FROM kurse WHERE datum=? and fondsid=?", (res["max(datum)"], ix), cursor=cursor)

        return erste, letzte


    @local_cursor_wrapper
    def isin_or_id_to_index(self, isin_or_id, cursor=None):
        if type(isin_or_id) is str:
            isin_id = self.isin2index(isin_or_id, cursor=cursor)
            assert isin_id is not None, "ISIN %s nicht in Kurse-DB" % isin_or_id
        else:
            isin_id = isin_or_id
        return isin_id

    @local_cursor_wrapper
    def insert_isin(self, isin, waehrung="EUR", cursor=None):
        cursor.execute(
            "INSERT INTO fonds (isin, waehrung) values (?,?)", (isin, waehrung))


    @local_cursor_wrapper
    def get_kurs_db(self, isin_or_id, datum, exact=True, cursor=None):
        isin_id = self.isin_or_id_to_index(isin_or_id, cursor=cursor)

        if exact:
            return self.fetchone("SELECT * FROM kurse WHERE datum=? AND fondsid=?",
                                 (datum, isin_id))

        return self.fetchone("SELECT * FROM kurse WHERE datum<=? AND fondsid=? ORDER BY datum DESC LIMIT 1",
                             (datum, isin_id), debug=False)

    @local_cursor_wrapper
    def get_last_kurs(self, isin_or_id, *, cursor=None):
        """ Hole den neusten Eintrag des Kurses aus der Datenbank

        :param isin_or_id: ISIN oder Index
        :type isin_or_id: str/int
        :param cursor: cursor, defaults to None
        :type cursor: cursor, optional
        :return: Datenbankeintrag oder None
        :rtype: Datenbankeintrag
        """
        isin_id = self.isin_or_id_to_index(isin_or_id, cursor=cursor)
        last = self.fetchone("SELECT max(datum) FROM kurse WHERE fondsid=?", (isin_id,), cursor=cursor)
        if last is None:
            return None
        return self.fetchone("SELECT * FROM kurse WHERE datum=? and fondsid=?", (last["max(datum)"], isin_id), cursor=cursor)

    @local_cursor_wrapper
    def get_alle_kurse(self, isin_or_id, *, start=None, ende=None, cursor=None):
        isin_id = self.isin_or_id_to_index(isin_or_id, cursor=cursor)

        querystart = "SELECT * FROM kurse WHERE fondsid=?"
        addwhere = ""
        queryende = " ORDER BY datum"
        params = [ isin_id ]
        if start is not None:
            addwhere += " AND datum >= ?"
            params.append(start)
        if ende is not None:
            addwhere += " AND datum <= ?"
            params.append(ende)

        query = querystart + addwhere + queryende
        return self.fetchall(query, params, debug=False)

    @local_cursor_wrapper
    def insert_kurse(self, isin_or_id, *, datalist, cursor=None):
        isin_id = self.isin_or_id_to_index(isin_or_id, cursor=cursor)
        for item in datalist:
            if type(item[KURSEDB_DATUM]) is datetime.datetime:
                datum = item[KURSEDB_DATUM].date()
            else:
                datum = item[KURSEDB_DATUM]
            query = "INSERT INTO kurse (datum, fondsid, schluss, stueck, volumen) VALUES (?,?,?,?,?)"
            params = (
                datum,
                isin_id,
                item[KURSEDB_SCHLUSSKURS],
                item.get(KURSEDB_STUECK),
                item.get(KURSEDB_VOLUMEN)
            )
            self.execute(query, params)
        self.commit()

    @local_cursor_wrapper
    def get_waehrungs_faktor(self, transaktionswaehrung, bewertungswaehrung, datum, cursor=None):
        if transaktionswaehrung == bewertungswaehrung:
            return 1.0
        wisin = bewertungswaehrung + transaktionswaehrung
        res = self.get_kurs(isin=wisin, datum=datum, cursor=cursor)
        if res is None:
            raise ValueError("Keine Umrechungseinträge für %s -> %s" % (transaktionswaehrung, bewertungswaehrung))
        return 1.0 / res[KURSEDB_SCHLUSSKURS]

    @local_cursor_wrapper
    def get_kurs(self, isin, datum, *, cursor=None):
        """Holt Kurs zu einem bestimmten Datum

        :param isin_or_id: ISIN
        :type isin_or_id: str or in
        :param datum: Datum
        :type datum: date
        :param cursor: cursor für Datenbank, defaults to None
        :type cursor: Cursor, optional
        :return: Datensatz mit `exact`-Eintrag oder None
        :rtype: dict
        :note: Falls ein Kurs zum angegebenen Datum nicht existiert,
        :note: wird `exact` auf False gesetzt und vom Datum davor zurückgegeben.
        :note: Falls er existiert, ist `exact` True
        """
        res = self.fetchone("SELECT * FROM fonds WHERE isin=?", (isin,), cursor=cursor)
        if res is None:
            return None
        isin_id = res[KURSEDB_FONDID]
        kurswaehrung = res[KURSEDB_KURSWAEHRUNG]

        res = self.fetchone("SELECT * FROM kurse WHERE datum=? AND fondsid=?",
                                 (datum, isin_id), cursor=cursor)
        if res is not None:
            res[KURSEDB_EXAKTES_DATUM] = True
        else:
            res = self.fetchone("SELECT * FROM kurse WHERE datum<=? AND fondsid=? ORDER BY datum DESC LIMIT 1",
                             (datum, isin_id), debug=False, cursor=cursor)

            if res is not None:
                res[KURSEDB_EXAKTES_DATUM] = False
        if res is not None:
            res[KURSEDB_KURSWAEHRUNG] = kurswaehrung
        return res

