# Konfigurationdatei

Zuerst sollte die Datei `config-beispiel.ini` nach `config.ini` kopiert werden.

(Linux)
```
cp config-beispiel.ini config.ini
```

Öffnen Sie die Datei mit einem Texteditor und passen Sie die Pfadnamen an.

# Daten

Erstellen Sie nun die Yaml-Dateien. (Beispiele finden Sie im Unterverzeichnis `beispiele`)

- Beginnen Sie zunächst mit `depots.yaml`.
  - Verpflichtend ist nur der Eintrag `name`.
- Als Nächstes sollten Sie die einzelnen Wertpapiere in ihren Depots definieren.
  - Für jedes Wertpapier sollten mindestens die Einträge `isin`, `name`, `kurswaehrung`, `teilfreistellung` und ggf. `thesaurierend` vorhanden sein.
- Am meisten Arbeit dürfte das Zusammentragen der Transaktionen machen. Käufe und Verkäufe kommen in die Datei `portfolio.yaml` und Ausschüttungen nach `ausschuettungen.yaml`.
  - Bei Käufen und Verkäufen sind die Einträge `typ`, `datum`, `depot`, `isin`, `kurs`, `anzahl` und `waehrung` notwendig.
  - Bei Ausschüttungen sind dies `typ`, `datum`, `depot`, `isin`, `betrag` und `waehrung`.

Eine genaue Beschreibung der Daten und Vorschläge für weitere optionale Einträge finden Sie [hier](daten.md).

# Kursdaten

Als abschließender Schritt müssen noch Kurs- und ggf. Währungsdaten in die Kursdatenbank eingelesen werden. Am einfachsten dürfte das im Augenblick durch heruntergeladene CSV-Datein von Onvista möglich sein (kostenlose Anmeldung erforderlich). Weitere Hinweise hierzu finden Sie [hier](kursdaten.md).

Sollten Transaktionen oder Kurse nicht in EUR angegeben sein, müssen zusätzlich Umrechnungskurse definiert werden. Siehe dazu auch [hier](daten.md#wertpapiere-mit-anderen-fondswährungen).

Auch das Einlesen von Indices ist [möglich](daten.md#indices).

Diese können bei [Kursvergleichen](kursdaten.md#unterbefehle-kursvergleich--kv) verwendet werden.

# Auswertung

Alle diese Daten sind für die Auswertung notwendig. Am häufigsten werden Sie wohl die Unterbefehle `kursvergleich` und `kv` verwenden.

Aber auch bei der Ermittlung der [Zahlen für die Steuererklärung](berechnungsgrundlagen.md) sind sie notwendig.

