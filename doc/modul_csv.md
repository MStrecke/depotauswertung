Dieses Modul ließt CSV-Dateien ein.

Hierzu werden die in der Konfigurationsdatei definierten [Verzeichnisse](kursdaten.md) durchsucht.

Je nach Quelle
* muss der Dateiname bestimmten Voraussetzungen entsprechen
* die zugehörigen Schlüssel in den [Stammdaten](daten.md) definiert sein
* Der Inhalt muss einem vordefinierten Schema folgen.

Andernfalls wird ein Fehler ausgegeben.

Aus den CSV-Dateien geht meistens nicht hervor, wie sie entstanden sind und welche Parameter gesetzt waren.

Es liegt also an Ihnen darauf zu achten, dass
* die Zahlen von der Fondsgesellschaft und nicht von einer Börse stammen
* keine Ausschüttungen eingerechnet sind
* möglichst in EUR angegeben sind

Die Währung, die in der CSV-Datei erwartet wird, haben Sie in den Stammdaten mit `kurs_waehrung` definiert.
Falls beispielsweise die CSV-Datei Kurse in USD enthält, obwohl EUR erwartet wird, stimmen die daraus abgeleiteten Berechnungen nicht.

Es ist zwar möglich Kurse mit anderen Währungen als EUR zu verarbeiten, dafür müssen aber die Tageskurse für eine Währungsumrechnung eingelesen werden, die eine weitere Unsicherheit für das Endergebnis einbringt.

Nach dem fehlerfreien Einlesen wird die Datei in das Unterverzeichnis `fertig` verschoben, damit sie nicht noch einmal eingelesen wird.

Außerdem wird geprüft, ob die eingelesenen Zahlen an die bereits gespeicherten Werte anschließen. D.h. es wird das letzte Datum in der Datei und dessen Kurs bestimmt. Dieses Datum und Kurs müssen auch in der CSV-Datei vorkommen.

Falls die Zahlen immer aus der gleichen Quelle stammen, ist das meist kein Problem.

Zahlen aus unterschiedlichen Quellen können sich aber in der Genauigkeit (3 oder 4 Nachkommastellen) unterscheiden. Deshalb existiert der optionalen Parameter `ignore`, mit dem Sie angeben können wie weit (absolut) der letzte gespeicherte und der entsprechende neue Wert voneinander abweichen dürfen.
