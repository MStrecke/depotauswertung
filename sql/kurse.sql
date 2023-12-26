CREATE TABLE fonds (
    fondsid integer primary key autoincrement,    -- interne ID für Wertpapier
    isin varchar(32) not null,                    -- ISIN des Fonds
    bezeichnung varchar(200) not null default "",
    waehrung varchar(5) not null default "EUR"    -- Währung der Einträge in der Datenbank
);
CREATE INDEX f_isin ON fonds(isin);

CREATE TABLE kurse (
    id integer primary key autoincrement,
    datum date not null,
    fondsid integer not null,
    schluss float not null,
    stueck float,
    volumen float,
    FOREIGN KEY(fondsid) REFERENCES fonds(fondsid)
);
CREATE INDEX k_isin ON kurse(fondsid);
CREATE INDEX k_datum ON kurse(fondsid, datum);