# For our english visitors

This program is based on German tax legislation and therefore only useful for Germans.  For this reason all messages, comments, and the documentation are in German.

# Warnung + Haftungsausschluss

Ich bin kein Steuerberater und die von diesem Programm ermittelten Zahlen sind nicht
verbindlich. Ich schließe hiermit ausdrücklich jede Haftung aus.

Die Kursdaten, die der Berechnung zugrunde liegen, haben einen großen Einfluss auf das Ergebnis. Je nach Quelle ist deren Qualität aber unterschiedlich, was zu leicht unterschiedlichen Ergebnissen führen kann.

Das Programm ist das Ergebnis einer ausgiebigen Internetrecherche. Ich bin bestrebt, die Zahlen so genau wie möglich zu ermitteln. Fehler kann ich aber nicht ausschließen. Deshalb  bin ich für jeden Hinweis dankbar.

# Zweck des Programms

Dieses Programm dient hauptsächlich zur Berechnung der Vorabpauschale und Aufsummierung von Ausschüttungen bei Depots sowie die Zuordnung von Verkäufen auf frühere Käufe.

Ausländische Banken machen das ggf. nicht automatisch und bei inländischen Banken kann man mit Kenntnis dieser Zahlen seinen Sparerfreibetrag besser anpassen.

# Benötigte Daten

Benötigt werden die Daten zu den Depots, den Wertpapieren, den An- und Verkäufen sowie zu den Ausschüttungen. Diese werden in Yaml-Dateien erfasst. Dies sind einfache Textdateien, die auch von Menschen lesbar sind und mit einem einfachen Texteditor aktualisiert werden können.

Eine genaue Beschreibung des Aufbaus der Dateien und welche Daten zwingend benötigt werden, finden Sie [hier](doc/daten.md).

Zur Bewertung und Ermittlung der Vorabpauschale werden außerdem die Kurse der Wertpapiere zu bestimmten Zeitpunkten benötigt. Diese Kurse können von entsprechenden Webseiten als CSV-Dateien geladen und in einer [Kursdatenbank](doc/kursdaten.md) gespeichert werden.

Die Bewertung erfolgt in EUR. Es können auch Wertpapiere in anderen Währungen verarbeitet werden, allerdings ist dazu das Einlesen einer tagesgenauen Umrechnung erforderlich, die aber auch weitere Ungenauigkeiten einbringt.

# Weitere Dokumentation

Ausführlichere Informationen finden Sie auf den folgenden Unterseiten:

* [Installation](doc/installation.md)
* [Erste Schritte](doc/first_steps.md)
* [Konfigurationdatei](doc/config.md)
* [Daten](doc/daten.md)
* [Kursdatenbank](doc/kursdaten.md)

# Programmfunktionen

 * Anzeigen der Stammdaten
 * Anzeigen der Transaktionen
 * Kursdatenbank
   * Anzeigen der ISINs in der Kursdatenbank
   * Abfrage eines Kurs aus der Kursdatenbank
   * Kursvergleich (grafisch)
   * Einlesen von CSV-Dateien
   * Einlesen von Online-Daten (experimentell)
 * Berechnung der Vorabpauschale
