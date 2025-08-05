#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Interaktives Skript zum Anlegen eines neuen Ausbilder‑Accounts.
Fragt Username und Passwort ab und legt den User in der DB an.
"""

import getpass
import sys
from app import app, db, User

def main():
    with app.app_context():
        # Username
        username = input("Neuen Benutzernamen eingeben: ").strip()
        if not username:
            print("Kein Username angegeben. Abbruch.")
            return

        # Prüfen, ob schon vorhanden
        if User.query.filter_by(username=username).first():
            print(f"Benutzer '{username}' existiert bereits.")
            return

        # Passwort (twice)
        pw1 = getpass.getpass("Passwort eingeben: ")
        pw2 = getpass.getpass("Passwort bestätigen: ")
        if pw1 != pw2:
            print("Fehler: Passwörter stimmen nicht überein.")
            return
        if not pw1:
            print("Kein Passwort angegeben. Abbruch.")
            return

        # User anlegen
        u = User(username=username)
        u.set_password(pw1)
        db.session.add(u)
        db.session.commit()
        print(f"Benutzer '{username}' wurde erfolgreich angelegt.")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print("Fehler beim Anlegen des Benutzers:", e)
        sys.exit(1)
