Dies sind Beispiel-Dateien.

Beachten Sie, dass die Zeilen mit den drei Bindestrichen `---` einen neuen Datensatz einleiten.

Die Dateien können beliebig benannt werden. Die Datei `config.ini` muss entsprechend angepasst werden.

`depots.yaml` definiert den Namen des/der Depot(s).
`stammdaten.yaml` beschreibt die einzelnen Wertpapiere.
`portfolio.yaml` beschreibt den Kauf und Verkauf von Anteilen.
`ausschuettungen.yaml` beschreibt die erhaltenen Ausschüttungen.

Der Aufbau dieser Dateien wird [hier](../doc/daten.md) genauer beschrieben.

Die Aufteilung der Transaktionen in `portfolio.yaml` und `ausschuettungen.yaml` hat eher organisatorische Gründe: Bei Sparplänen findet man einfacher die letzte (ähnliche) Transaktion und kann eine neue mit Kopieren/Einfügen am Ende hinzufügen und dann nur die geänderten Daten editieren (Datum, Kurs, Anzahl, ID).

Ähnliches gilt für die Ausschüttungen.
