# Kurse

Eintrag in der Konfigdatei: `[databases] kurse`

Die historischen Kurse werden in dieser Sqlite-Datenbank gespeichert. Der Aufbau ist in `sql/kurse.sql` definiert.

Die hier gespeicherten Daten stammen hauptsächlich aus CSV-Dateien der entsprechenden Websites. Die Qualität der dort heruntergeladenen Daten bestimmt auch die Berechnung.

Neben Fonds und ETFs können auch Währungen und Indizes gespeichert werden.

Bei Fonds und ETFs ist darauf zu achten, dass die Währung dem Eintrag `kurswaehrung` in den Stammdaten entspricht. Auch sollten zur besseren Vergleichbarkeit die Kurse von einer Fondsgesellschaft und nicht von einer Börse stammen und keine Ausschüttungen enthalten.

# CSV-Dateien einlesen

Zurzeit können CSV-Dateien von Onvista und Ariva eingelesen werden. Hierzu muss in der Konfigurationsdatei der Abschnitt `[onvista]` bzw. `[ariva]` angelegt werden und dort der Schlüssel `csv_verzeichnis` definiert werden.

Beispiel:
```
[onvista]
csv_verzeichnis=~/fonds/csv/onvista

[ariva]
csv_verzeichnis=~/fonds/csv/Ariva
```

Mit dem Befehl `csv` wird das entsprechende Verzeichnis nach Dateien durchsucht und es wird versucht, diese einzulesen.

Erfolgreich eingelesene Dateien werden in das Unterverzeichnis `fertig` verschoben, damit sie nicht noch einmal eingelesen werden.

Es können aber auch Probleme auftreten, wenn
 * die CSV-Datei nicht dem vorgegebenen Format entspricht
 * die Daten nicht nahtlos an die bereits gespeicherten Daten anschließen

Siehe hierzu auch die Beschreibung im zugehörigen [Modul](modul_csv.md).

# Unterbefehl: refresh

Diese Funktion ist experimentell, da sie eine inoffizielle Möglichkeit der Onvista-Webseite nutzt, Daten abzufragen. Durch eine Änderung an der Onvista-Website kann diese Funktion jederzeit ohne Vorwarnung wegfallen.

Sie benötigt zusätzlich die Einträge `onvista_entity` und `onvista_notation` in den Wertpapier-Stammdaten. `onvista_notation` ist Teil des Dateinamens, wenn man eine CSV-Datei herunterlädt; `onvista_entity` lässt sich hingegen nur umständlich, z. B. durch Beobachten des Übertragungsprotokolls des Browsers, ermitteln.

Der Download per CSV ist zwar umständlicher aber sicherer.

# Unterbefehle: kursvergleich + kv

Diese beiden Befehle werten die Kursdatenbank aus und stellen sie grafisch dar.

Dabei werden Fremdwährungen nach EUR umgerechnet.

Ausnahme: Indices mit der Währung `Pkt.`. Diese werden 1:1 dargestellt.

## kursvergleich

Die Entwicklung (absolut und prozentual) lässt sich mit dem Unterbefehl `kursvergleich` darstellen. Benötigt wird das Startdatum und die ISINs. Die Daten kommen aus der lokalen `kursdatenbank`.

Aufgerufen wird die Funktion mit:

```
kursvergleich datum ISIN1 ISIN2 ISIN3 ...
```

Die Option `--savesvg` speichert die Grafik im Verzeichnis `/tmp`.


## kv

Häufig durchgeführte Kursvergleiche können in der Konfigurationsdatei im Abschnitt `kursvergleiche` in der folgenden Form programmiert werden:

```
[kursvergleiche]
ID=datum ISIN1 ISIN2 ISIN3 ...
```

Das `datum` (TT.MM.JJJJ) ist dabei optional.

Aufgerufen wird die Funktion mit dem Befehl:

```
kv ID
```

oder

```
kv ID datum
```

Ein beim Aufruf angegebenes `datum` überschreibt das (optional) in der Konfigurationsdatei angegebene Datum.

Auch dieser Befehl kennt die Option `--savesvg`.
