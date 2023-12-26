# Daten

Die Dateinamen der verwendeten Dateien werden in `config.ini` [definiert](config.md).

Die Stammdaten, die Daten für Käufe/Verkäufe und für Ausschüttungen müssen im Yaml-Format vorliegen. Dieses Format ist auch von Menschen lesbar. Es kann einfach mit einem Texteditor bearbeitet und ergänzt werden. Normalerweise sind das nur wenige Zeilen im Monat.

Im Unterverzeichnis `beispiele` finden Sie einige Beispiele.

Die Zahlen liegen im "deutschen Format" vor, d.h. mit Dezimalkomma.

Einige Schlüssel in der Yaml-Datei sind zwingend vorgeschrieben, da sie vom Programm zur Berechnung oder Anzeige verwendet werden. Die restlichen Schlüsselnamen können frei vergeben werden, um weitere Informationen aufnehmen.

Für die Kurse pflegt das Programm eine lokale Sqlite-Datenbank. Die Datenbank kann mit Daten aus unterschiedlichen Quellen gefüllt werden. Welche Quelle das ist, hängt von Ihnen ab.

Es hat sich gezeigt, dass die Genauigkeit der Daten von Quelle zu Quelle unterschiedlich ist. Schon aus diesem Grund kann es zu Abweichungen bei der Berechnung kommen.

Die Kurse werden sowohl zur Berechnung als auch zur Visualisierung herangezogen.

# Yaml-Dateien

Yaml-Dateien sind Textdateien, die mit einem Texteditor bearbeitet werden können.

## Aufbau

Das Programm verwendet nur einen kleinen Ausschnitt der Yaml-Spezifikation:
* Die Zeilen sind nach dem Format `Schlüssel: Wert` aufgebaut.
* Ein neuer Datensatz beginnt mit einer Zeile mit drei Bindestrichen `---`.

```
schluessel1: wert1
schluessel2: wert2
schluessel3: wert3
---
schluessel1: wert4
schluessel2: wert5
schluessel3: wert6
---
usw.
```

Weiter unten wird beschrieben, welche Schlüssel vorgeschrieben (mit einem `M` gekennzeichnet) und welche optional sind (`O`).

## Plausibilitätsprüfungen

Beim Start des Programms werden die Yaml-Dateien auf das Vorhandensein der vorgeschriebenen Schlüssel und deren Werte auf entsprechende Vorgaben überprüft (z. B. Datum auf das Format: TT.MM.JJJJ).

Die internationale Wertpapierkennung (ISIN) besitzt eine Prüfziffer, die vom Programm ebenfalls an vielen Stellen überprüft wird.

Bei Fehlern gibt das Programm eine entsprechende Meldung aus.

## Depots

Eintrag in der Konfigdatei: `[data] depots`

Jeder Yaml-Eintrag hat nur eine vorgeschriebene Position:

| Name        | M/O | Bedeutung
| ----------- |:---:| ---------
| name        |  M  | ID des Depots in den anderen Daten

Der hier definierte Name wird verwendet, um Käufe, Verkäufe und Ausschüttungen einem Depot zuzuordnen.

Man **kann** hier weitere Infos erfassen, die aber vom Programm nicht ausgewertet werden, z. B.:

| Name        | M/O | Bedeutung
| ----------- |:---:| ---------
| kontonummer |  O  | Kontonummer des Verrechnungskontos bei der Bank
| währung     |  O  | Währung des Verrechnungskontos

## Daten zu Wertpapieren

Eintrag in der Konfigdatei: `[data] wertpapiere_stammdaten`

Basisinfos zu den Wertpapieren

| Name                | M/O | Bedeutung
| ------------------- |:---:| ---------
| isin                |  M  | ID des Wertpapiers
| name                |  M  | Name des Wertpapiers
| kurswaehrung        |  M  | sollte EUR sein, Währung des Fonds in der Datenbank und auf Abrechnungen
| teilfreistellung    |  M  | 30%, 15%, 0% (Verwendung bei Basisertragsberechnung)
| typ                 |  M  | "ETF", "Fonds", "currency", "index"
| thesaurierend       |  O  | thesaurierend (true) oder ausschüttend (false)

Der Wert `thesaurierend` wird zwar nicht zur Berechnung verwendet, erscheint aber in einigen Ausgaben und sollte deshalb vorhanden sein.

Der Wert `typ` steuert, welche Informationen beim Einlesen der Kurse erwartet werden und ob die ISIN geprüft werden muss.

### Wertpapiere mit anderen Fondswährungen

Das Programm unterscheidet mehrere Währungen:

* `kurswaehrung`: Währung der Kurse dieser ISIN in der Kursdatenbank - erforderliche Angabe in den Wertpapierstammdaten
* `fondswaehrung`: Währung in der der ETF/Fonds aufgelegt ist (z.B. USD bei vielen MSCI World ETFs) - diese Angabe dient nur der Information und wird bei den Berechnungen **nicht** verwendet.
* Währung der Auswertungen: immer "EUR" - Währung bei Berechnung der Vorabpauschale oder im letzten Feld des Kursvergleichs.

| Name                | M/O | Bedeutung
| ------------------- |:---:| ---------
| fondswaehrung       |  O  | Fondswährung (z.B. EUR, USD)

`kurswaehrung` und `fondwaehrung` müssen nicht unbedingt identisch sein. Meist lassen sich CSV-Dateien bei Wertpapieren in USD auch in EUR herunterladen (`KSV (EUR)` statt `KSV (USD)`).

Falls die `kurswaehrung` eines Wertpapiers nicht `EUR` ist, also z. B. `USD`, dann **müssen** für die Funktion "kursvergleich" und "vorab" auch Tages-Umrechnungskurse in der Kursdatenbank gespeichert sein.

Hierzu wird zunächst ein Datensatz in den Stammdaten angelegt:
 * Die ISIN dieser Umrechnungskurse ist festgelegt: `EURxxx`
   * Bei USD also "EURUSD" (1 EUR entspricht x USD).
 * Der `typ` muss auf `currency` gesetzt werden.

Eine solche Umrechnung macht das Ergebnis ungenauer.

### Indices

Auch Indices, z. B. der MSCI World, kann in den Stammdaten definiert werden. Danach kann er als CSV-Datei eingelesen und bei Kursvergleichen verwendet werden.

Zu beachten ist:
 * Die ISIN kann frei gewählt werden, z. B. "MSCI World".
 * Der `typ` muss auf `index` gesetzt werden.
 * Die `waehrung` ist meist `Pkt.`

### Schlüssel zum Einlesen von CSV-Dateien von Ariva

Der Name der von Ariva gelieferten CSV-Datei hat den folgenden Aufbau: `wkn_XXXXXX_historic.csv`.

Dabei ist XXXXXX die `wkn`. Um die ISIN zu ermitteln, muss sie deshalb in den Stammdaten definiert werden:

| Name             | M/O | Bedeutung
| ---------------- |:---:| ---------
| wkn              |  O  | WKN des Wertpapiers

Siehe auch die Hinweise zu CSV-Dateien in [kursdaten](kursdaten.md).

### Schlüssel zum Einlesen von CSV-Dateien von Onvista

Der Name der von Onvista gelieferten CSV-Datei begint mit: `history_########-`. Dabei ist ######## der im Folgenden definiert Wert `onvista_notation`:

| Name             | M/O | Bedeutung
| ---------------- |:---:| ---------
| onvista_notation |  O  | wahrscheinlich ID des Handelsplatzes

#### Online-Abfrage

Es ist möglich, der Onvista-Website Kursdaten zu entlocken. Der hierfür notwendige Wert `onvista_entity` ist jedoch nur sehr schwierig zu ermitteln und sollte deshalb nur von Spezialisten verwendet werden:

| Name             | M/O | Bedeutung
| ---------------- |:---:| ---------
| onvista_entity   |  O  | wahrscheinlich ID des Wertpapiers

Siehe auch [hier](kursdaten.md#unterbefehl-refresh).

# Käufe und Verkäufe

Eintrag in der Konfigdatei: `[data] portfolio`

Die Yaml-Datei beinhaltet die Käufe und Verkäufe von Wertpapieren.

| Name             | M/O | Bedeutung
| ---------------- |:---:| ---------
| typ              |  M  | Typ des Eintrags: kauf, verkauf
| datum            |  M  | Format: TT.MM.JJJJ
| depot            |  M  | ID des Depots
| isin             |  M  | ID des Wertpapiers
| anzahl           |  M  | verkaufte/gekaufte Anzahl (Dezimalkomma)
| kurs             |  M  | Verkaufs-/Kaufkurs (Dezimalkomma)
| waehrung         |  M  | Währung des Verkaufs/Kaufs (EUR)

Vorschlag für weitere Einträge, die nützlich sein können:

| Name             | M/O | Bedeutung
| ---------------- |:---:| ---------
| tid              |  O  | ID der Transaktion
| kosten           |  O  | Weitere Kosten des Kaufs/Verkaufs

# Ausschüttungen

Eintrag in der Konfigdatei: `[data] ausschuettung`

Diese Yaml-Datei nimmt die von ausschüttenden Wertpapieren erhaltenen Beträge auf.

| Name             | M/O | Bedeutung
| ---------------- |:---:| ---------
| typ              |  M  | Typ der Transaktion: ausschuettung
| datum            |  M  | Format: TT.MM.JJJJ
| depot            |  M  | ID des Depots
| isin             |  M  | ID des Wertpapiers
| betrag           |  M  | erhaltener Betrag (Dezimalkomma)
| waehrung         |  M  | Währung (EUR)

Vorschlag für weitere Einträge:

| Name             | M/O | Bedeutung
| ---------------- |:---:| ---------
| ref              |  O  | ID der Transaktion
| bemerkung        |  O  | interne Bemerkung

