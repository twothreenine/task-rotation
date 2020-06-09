# Einstieg
Mit einer Taskrotation-Tabelle lassen sich Aufgaben, die sich regelmäßig wiederholen, innerhalb einer Gruppe automatisch zuweisen.
Zunächst werden die **Teilnehmer_innen** der Gruppe eingetragen und eine oder mehrere wiederkehrende Aufgaben als **Aufgabentypen** definiert. Daraufhin werden durch Ausführung des Skriptes automatisch **Termine** für die nächste Zeit generiert und, je nach Bedarf, jeweils bis zu fünf Verantwortliche für den Dienst zugewiesen. Außerdem können **Hinweise** definiert werden, die wiederum in eigenen Abständen bestimmten Terminen automatisch beigefügt werden - z.B. anfallende Zusatzaufgaben oder was für einen bestimmten Termin zu beachten ist.

## Features
* Aufzeichnung wer schon wie oft dran war
* Automatische Zuweisung bevorzugt von Teilnehmer_innen, die unverhältnismäßig selten oder schon lange nicht mehr dran waren
* Unterscheidung von Teilnehmer_innen, die sich auskennen; wie viele erfahrene Personen (die sich auskennen) und wie viele insgesamt für einen bestimmten Termin nötig sind
* Optionen für Wiederholung von Aufgabentypen: alle n Tage/Monate/Jahre, am x-ten (Wochen-)Tag der Zeitperiode (Beispiel: alle 7 Tage am 2., 4. und 6. Tag)
* Optionen für Wiederholung von Hinweisen: alle n Tage/Monate/Jahre, am x-ten Termin eines Aufgabentyps (oder mehreren) innerhalb der Zeitperiode (Beispiel: am letzten Termin jeden Monats)
* Manuelle Änderung des Datums bei von der Regel abweichenden Terminen, ohne dass Folgetermine beeinflusst werden
* Manuelle Änderung/Tauschen der zugewiesenen Personen
* Zellen, die nur automatisch geändert werden sollen bzw. Formeln enthalten, sind vor versehentlicher Manipulation geschützt (können aber von jeder Benutzer_in entsperrt werden)
* Benachrichtigungen über automatisch erfolgte Zuweisungen, Erinnerungen an bevorstehendene Termine und Rückfragen, ob Dienste ausgeführt wurden (in Kombination mit einem Modul, das über ein bestimmtes Medium Nachrichten/E-Mails verschickt)
* Lokales Backup der Tabelle im Socialcalc-Format immer vor und/oder nach der Ausführung des Skriptes anlegen, bzw. auf Anforderung
* Import einer Tabelle, die zuvor im Socialcalc-Format exportiert wurde

## Sprachen
* Verfügbare Sprachpakete für Blanko-Tabelle und Nachrichten
    * Englisch (en)
    * Deutsch - Österreich (de_AT)
* Hinweis: Bestimmte Ausdrücke müssen in der Tabelle in Englisch eingegeben werden, z.B. die Zeitperiode als day, month oder year

## Verfügbare Module für Benachrichtigungen
* Foodsoft (getestet für v4.6.99) - aktuell noch direkt in Taskrotation integriert, soll aber ausgelagert werden

## Was die Tabelle (noch) nicht kann
* Mehr als fünf Personen zu einem Termin zuweisen
* Anzahl der ausgeführten Dienste je nach Aufgabentyp zählen und bevorzugt Teilnehmer_innen zuweisen, die jenen Aufgabentyp noch nicht so oft hatten
* Erfahrung ("kennt sich aus") je nach Aufgabentyp unterscheiden; unterschiedliche Stufen von Erfahrungen bzw. verschiedene Kenntnisse unterscheiden
* Namen von Teilnehmer_innen automatisiert ändern (wird ein Name in der Untertabelle Teilnehmer_innen geändert, muss er auch bei allen Terminen, bei denen die Person zugewiesen ist/war, geändert werden)
* Dienste abhaken, nachdem sie ausgeführt werden (das Skript geht davon aus, dass vergangene Termine von den zugewiesenen Personen erledigt wurden, die können aber auch bei vergangenen Terminen noch manuell geändert werden; deswegen wird in der "Rückfrage-Mail" dazu aufgerufen die Namen zu ändern, falls der Dienst nicht oder von jemand anderem ausgeführt wurde)
* Ergebnisse von Diensten/Terminen dokumentieren (außer per Hinweise-Spalte)
* Teilaufgaben

## Zu beachten - Kurzfassung
* Datumsangaben in der Tabelle immer als JJJJ-MM-TT eingeben
* Namen der Teilnehmer_innen müssen immer exakt so geschrieben werden, wie sie in der Teilnehmer_innen-Untertabelle eingetragen sind
* Besser keine Zeilen löschen, z.B. wenn ein Termin entfällt, ein_e Teilnehmer_in ausscheidet oder ein regelmäßiger Hinweis wegfällt. Stattdessen End-Datum / "aktiv bis" eintragen bzw. bei Terminen 0 benötigte Personen angeben und in der Spalte "Zeile ausblenden?" TRUE eintragen

# Schritt für Schritt
folgt noch ...