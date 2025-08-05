# T-CPR (Telefonreanimation) - Qualitätsmanagement Tools für deutschsprachige Leitstellen
Ein Tool um Telefonreanimationen mit Qualitätsmanagementfaktoren zu bewerten und Feedback an Disponenten zu geben.

# T-CPR QM Training – Installations­anleitung

## Inhaltsverzeichnis
1. [Voraussetzungen](#voraussetzungen)  
2. [Automatische Installation](#automatische-installation)  
3. [Domain-Konfiguration](#domain-konfiguration)  
4. [Admin-Benutzer anlegen](#admin-benutzer-anlegen)  
5. [Datenbank-Schema](#datenbank-schema)  
6. [Sicherheit & Tipps](#sicherheit--tipps)  

---

## Voraussetzungen
- Ubuntu/Debian Server mit SSH-Zugang (sudo-Rechte)  
- DNS-Eintrag für eure Domain auf diesen Server  

---

## Automatische Installation
Im Projekt-Root liegt ein Skript `install.sh`. Mach es ausführbar und starte es:

```bash
sudo chmod +x install.sh
sudo ./install.sh
Was das Skript erledigt:

Installiert System-Pakete:
python3, python3-venv, python3-pip, git, nginx, wkhtmltopdf

Klont (oder updated) das Git-Repo unter /var/www/reatraining

Legt ein Python-Virtualenv an und installiert requirements.txt

Erstellt eine .env mit:

FLASK_SECRET_KEY

DATABASE_URL

WKHTMLTOPDF_PATH

Initialisiert die SQLite-Datenbank (db.sqlite3)

Setzt Dateiberechtigungen (nur www-data darf lesen)

Erzeugt und startet einen systemd-Service (reatraining.service)

Konfiguriert und aktiviert eine nginx-Site

Domain-Konfiguration
Öffne /etc/nginx/sites-available/reatraining und passe server_name an:

nginx
Kopieren
Bearbeiten
server {
    listen 80;
    server_name deine.domain.tld;
    …
}
Dann:

bash
Kopieren
Bearbeiten
sudo nginx -t
sudo systemctl reload nginx
Admin-Benutzer anlegen
bash
Kopieren
Bearbeiten
cd /var/www/reatraining
source venv/bin/activate
python create_user.py
deactivate
Folge den Eingabe-Aufforderungen für Nutzername & Passwort.

Datenbank-Schema
Tabelle session
Spalte	Typ	Beschreibung
id	INTEGER PK	Primärschlüssel
trainer	TEXT	Ausbilder (Flask-Login)
disponent	TEXT	Disponenten-Name
start_time	DATETIME	Startzeitpunkt
end_time	DATETIME	Endzeitpunkt
total_sec	INTEGER	Gesamtdauer in Sekunden

Tabelle step
Spalte	Typ	Beschreibung
id	INTEGER PK	Primärschlüssel
session_id	INTEGER FK	Verweis auf session.id
name	TEXT	QM-Maßnahme
cumulative	INTEGER	Kumulative Zeit in Sekunden
interval	INTEGER	Intervall seit letzter Maßnahme (s)
out_of_order	BOOLEAN	Reihenfolgeabweichung

Tabelle feedback
Spalte	Typ	Beschreibung
id	INTEGER PK	Primärschlüssel
session_id	INTEGER FK	Verweis auf session.id
timestamp	DATETIME	Zeitstempel des Feedbacks
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
.env nicht ins Git-Repo committen.

Berechtigungen für DB-Datei:

bash
Kopieren
Bearbeiten
sudo chown www-data:www-data /var/www/reatraining/db.sqlite3
sudo chmod 640 /var/www/reatraining/db.sqlite3
In Produktionsumgebungen: Nutzt einen Secret-Manager (Vault, AWS Secrets Manager).

Firewall: Öffnet nur HTTP/HTTPS (Ports 80/443), SSH idealerweise nur für bestimmte IPs.

Backups: Regelmäßige Sicherung von db.sqlite3.

Mit diesen Schritten ist eure Anwendung produktions­bereit und sicher aufgesetzt.
Viel Erfolg bei eurem QM-Training! 🎉
