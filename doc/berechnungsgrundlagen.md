# Kurse

Bei Käufen und Verkäufen ist der tatsächliche Kurs auf der Abrechnung angegeben und wird in die Yaml-Daten übernommen.

Diese 'tatsächlichen' Kurse werden nur an zwei Stellen verwendet:
* bei der Berechnung des realisierten Gewinns/Verlusts
* bei der Berechnung der Wertsteigerung, wenn der Kauf im Jahr stattfand

Ansonsten werden die Kurse aus der Kursdatenbank verwendet.
Insbesondere bei der Berechnung des Basisertrags.

# Wertsteigerung

Im Laufe des Jahrs verkaufte (realisierte) Anteile werden nicht berücksichtigt.

Der Anfangswert ist entweder
* der Kurs aus der Kursdatenbank, wenn die Anteile zum Jahresanfang im Portfolio waren, multipliziert mit der Anzahl der noch verbliebenen Anteile aus der Tranche
* der Kurs der Anteil, zu dem sie gekauft wurden, falls sie während des Jahres gekauft wurden, multipliziert mit der Anzahl der noch verbliebenen Anteile aus der Tranche

Der Endwert ist der Kurs der noch verbliebenen Anteile aus der Tranche multipliziert mit dem Kurs aus der Kursdatenbank.

Die Wertsteigerung ist: Endwert - Anfangswert

# Vorabpauschale

Quelle: https://www.finanztip.de/indexfonds-etf/etf-steuern/vorabpauschale/

Diese Berechnung wird in EUR vorgenommen und benutzt nur Kurse aus der Kursdatenbank, ggf. einschließlich zur Währungsumrechnung.

## Berechungsformeln

Vorabpauschale bei (ausschüttenden) Fonds

| Variable            | Erklärung
| ------------------- | --------------------------------------------
| einstandskurs       | Kurs zu dem der Fonds gekauft wurde
| einstandsdatum      | Datum zu dem der Fonds gekauft wurde
| verkaufskurs        | Kurs zu dem der Fonds verkauft wird
| KA                  | Kurs des Fonds zum Jahresanfang (aus Kursdatenbank)
| KE                  | Kurs des Fonds zum Jahresende (aus Kursdatenbank)
| anz                 | Anzahl der (verbliebenen) Anteile
| ausschüttungen      | Ausschüttungen im laufenden Jahr, 0 bei thesaurierenden Fonds
| teilfreistellung    | Teilfreistellung des Fonds (30%, 15%, 0%)
| für_die_steuer      | für die Steuer relevanter Betrag (nach der Teilfreistellung aber vor Abzug des Sparerfreibetrags)

## Fall 1: Fonds werden das ganze Jahr gehalten

Basisertrag = KA * anz * Basiszins * 0,7
Wertzuwachs = (KE - KA) * anz

### Berechnung

vorabpauschale = min(Basisertrag, Wertzuwachs)

wenn Wertzuwachs < 0:
  vorabpauschale = 0

wenn ausschüttungen >= vorabpauschale:
  vorabpauschale = 0
  für_die_steuer = ausschüttungen * (100% - teilfreistellung)
sonst
  vorabpauschale = vorabpauschale - ausschüttungen
  für_die_steuer = (vorabpauschale + ausschüttungen) * (100% - Teilfreistellung)

## Fall 2: Fonds werden im Jahr gekauft (z. B. Sparplan)

monatsfaktor = (13 - Monat des Einstandsdatums) / 12
=> Jan: 12/12, Feb: 11/12, März: 10/12 ...

// Achtung: Kurs zum 1.1. (nicht Kaufkurs!)
Basisertrag = KA * anz * Basiszins * 0,7 * Monatsfaktor

// Achtung: hier wird der tatsächliche Kaufkurs verwendet
Wertzuwachs = (KE - kaufkurs) * anz

Weitere `Berechnung`, wie [oben](#Berechnung).

## Fonds werden im Jahr verkauft

vorabpauschale = 0
wertzuwachs = 0

für_die_steuer = (verkaufskurs - einkaufskurs) * anz * (100% - Teilfreistellung) - Summe(Vorabpauschalen früherer Jahre)

# Zu zahlende Steuer

Hinweis:
Das Programm berechnet nur die Werte aufgrund der Vorabpauschale und der Ausschüttungen. Die Kombination der beiden, sowie der Abzug des Sparerfreibetrags und früherer Vorabpauschalen muss manuell vorgenommen werden.

  Summe aller Bemessungsgrundlagen
+ Summe aller anderen Zinseinkünfte
- Sparerfreibetrag
=
* Steuersatz (26,375%)

