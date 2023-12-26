`config.ini` ist die zentrale Konfigurationsdatei.

Die Einträge sind im bekannten INI-Format gespeichert und können mit einem beliebigen Texteditor angepasst werden.

# Abschnitte: [databases] und [data]

Diese Abschnitte sind zwingend vorgeschrieben. `databases` enthält den Pfad zur Kursdatenbank, `data` die Pfade auf die entsprechenden Yaml-Datendateien. Die Pfade können auch mit einem "~" beginnen. Der Aufbau der Yaml-Dateien wird [hier](daten.md) genauer beschrieben.

# Abschnitte [onvista] und [ariva]

Diese Abschnitte sind zwar optional, aber um Daten aus CSV-Dateien der entsprechenden Webseiten in die Kursdatenbank einzulesen, werden sie gebraucht. Siehe auch [hier](kursdaten.md). Die Daten werden in der unter `databases` definierten Kursdatenbank gespeichert.

# Abschnitt [kursvergleiche]
In diesem Abschnitt können häufig genutzte Kursvergleiche definiert werden, die mit dem Unterbefehl `kv` abgerufen werden können. Mehr Infos finden Sie [hier](kursdaten.md#unterbefehl-kv).

# Beispiel einer Konfigurationsdatei

```
[databases]
kurse=~/fonds/kurse.db

[data]
depots=~/fonds/depots.yaml
wertpapiere_stammdaten=~/fonds/wertpapiere_stammdaten.yaml
portfolio=~/fonds/portfolio.yaml
ausschuettung=~/fonds/ausschuettung.yaml
waehrung=~/fonds/waehrung.yaml

[onvista]
csv_verzeichnis=~/fonds/csv/onvista

[ariva]
csv_verzeichnis=~/fonds/csv/Ariva

[kursvergleiche]
test=10.08.2023 LU1437016972 LU0565419693 LU0119196268
postbank=IE00B4L5Y983 IE00BGHQ0G80
```