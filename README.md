# T-CPR (Telefonreanimation) - Qualitätsmanagement Tools für deutschsprachige Leitstellen
Ein Tool um Telefonreanimationen mit Qualitätsmanagementfaktoren zu bewerten und Feedback an Disponenten zu geben.

# T-CPR QM-Training – Installations­anleitung

## Inhaltsverzeichnis
1. [Voraussetzungen](#voraussetzungen)  
2. [Automatische Installation](#automatische-installation)  
3. [Domain-Konfiguration](#domain-konfiguration)  
4. [Admin-Benutzer anlegen](#admin-benutzer-anlegen)  
5. [Datenbank-Schema](#datenbank-schema)  
6. [Sicherheit & Tipps](#sicherheit--tipps)  

---

## Voraussetzungen
- **Betriebssystem:** Ubuntu 20.04+ oder Debian 10+  
- **Zugang:** SSH mit sudo-Rechten  
- **Domain:** DNS-Eintrag für eure Wunsch-Domain oder IP auf den Server  

---

## Automatische Installation
Im Projekt-Root liegt das Skript `install.sh`. So setzt ihr es auf:

```bash
cd /var/www/reatraining
sudo chmod +x install.sh
sudo ./install.sh
````

Das Skript erledigt:

Installation von System-Paketen
(python3, python3-venv, python3-pip, git, nginx, wkhtmltopdf)

Klonen bzw. Update des Git-Repos unter /var/www/reatraining

Anlegen eines Python-Virtualenv & Installation aller Abhängigkeiten

Erzeugen einer .env mit

FLASK_SECRET_KEY

DATABASE_URL

WKHTMLTOPDF_PATH

Initialisierung der SQLite-Datenbank (db.sqlite3)

Setzen der Dateiberechtigungen (nur www-data darf lesen)

Anlegen und Start eines systemd-Services reatraining.service

Konfiguration & Neustart von nginx

Domain-Konfiguration
Öffnet /etc/nginx/sites-available/reatraining und passt server_name an:
```bash
nginx
Kopieren
Bearbeiten
server {
    listen 80;
    server_name deine.domain.tld;
    ...
}
```
Dann:


Kopieren
Bearbeiten
sudo nginx -t
sudo systemctl reload nginx
Admin-Benutzer anlegen
Erstellt euren ersten Login-User mit dem Hilfs­script:

```bash
Kopieren
Bearbeiten
cd /var/www/reatraining
source venv/bin/activate
python create_user.py
deactivate
Folgt den Eingabe­aufforderungen für Nutzername & Passwort.
```

Datenbank-Schema
Tabelle session
Spalte	Typ	Beschreibung
id	INTEGER PK	Primärschlüssel
trainer	TEXT	Ausbilder-Username
disponent	TEXT	Disponenten-Name
start_time	DATETIME	Startzeit
end_time	DATETIME	Endzeit
total_sec	INTEGER	Gesamtdauer in Sekunden

Tabelle step
Spalte	Typ	Beschreibung
id	INTEGER PK	Primärschlüssel
session_id	INTEGER FK	Verweis auf session.id
name	TEXT	QM-Maßnahme
cumulative	INTEGER	Kumulative Zeit in Sekunden
interval	INTEGER	Intervall seit vorheriger Maßnahme
out_of_order	BOOLEAN	Reihenfolgeabweichung

Tabelle feedback
Spalte	Typ	Beschreibung
id	INTEGER PK	Primärschlüssel
session_id	INTEGER FK	Verweis auf session.id
timestamp	DATETIME	Zeitstempel Feedback
pos_situation	TEXT	Positive Situation (SBI)
pos_behavior	TEXT	Positive Behavior (SBI)
pos_impact	TEXT	Positive Impact (SBI)
neg_situation	TEXT	Negative Situation (SBI)
neg_behavior	TEXT	Negative Behavior (SBI)
neg_impact	TEXT	Negative Impact (SBI)
smart_goal	TEXT	SMART-Ziel
support	TEXT	Unterstützungsmaßnahmen
next_steps	TEXT	Nächste Schritte
overall	TEXT	Gesamtbewertung

Sicherheit & Tipps
.env nie ins Git-Repo committen.

DB-Zugriffsrechte für SQLite:

bash
Kopieren
Bearbeiten
sudo chown www-data:www-data /var/www/reatraining/db.sqlite3
sudo chmod 640 /var/www/reatraining/db.sqlite3
Secret-Management: In größeren Umgebungen lieber Vault oder AWS Secrets Manager nutzen.

Firewall: Öffnet nur HTTP/HTTPS (Ports 80/443), SSH idealerweise nur für Admin-IP.

Backups: Regelmäßige Sicherung der db.sqlite3.

🎉 Fertig! Eure T-CPR QM-Training-App ist nun vollständig installiert und sicher konfiguriert. Viel Erfolg!
