#!/usr/bin/env bash
set -e

# === Variablen ===
APP_DIR=/var/www/reatraining
REPO_URL=https://github.com/your_org/reatraining.git
ENV_FILE=$APP_DIR/.env

# 1) System-Pakete installieren
apt update
apt install -y python3 python3-venv python3-pip git nginx wkhtmltopdf

# 2) Repo klonen oder aktualisieren
if [ ! -d "$APP_DIR" ]; then
  git clone "$REPO_URL" "$APP_DIR"
else
  cd "$APP_DIR"
  git pull origin main
fi

# 3) Virtualenv & Abhängigkeiten
cd "$APP_DIR"
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
deactivate

# 4) .env anlegen (falls noch nicht vorhanden)
if [ ! -f "$ENV_FILE" ]; then
  cat > "$ENV_FILE" <<EOF
FLASK_SECRET_KEY=$(openssl rand -hex 32)
DATABASE_URL=sqlite:///$APP_DIR/db.sqlite3
WKHTMLTOPDF_PATH=$(which wkhtmltopdf)
EOF
  chmod 600 "$ENV_FILE"
fi

# 5) Datenbank initialisieren (falls neu)
if [ ! -f "$APP_DIR/db.sqlite3" ]; then
  source venv/bin/activate
  python3 - <<PYCODE
from app import db, app
with app.app_context():
    db.create_all()
PYCODE
  deactivate
fi

# 6) Rechte setzen (nur www-data darf lesen)
chown -R www-data:www-data "$APP_DIR"
find "$APP_DIR" -type d -exec chmod 750 {} \;
find "$APP_DIR" -type f -exec chmod 640 {} \;

# 7) systemd-Service erstellen
cat > /etc/systemd/system/reatraining.service <<'EOF'
[Unit]
Description=T-CPR QM Flask App
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/reatraining
EnvironmentFile=/var/www/reatraining/.env
ExecStart=/var/www/reatraining/venv/bin/gunicorn -w 3 --bind unix:/var/www/reatraining/reatraining.sock app:app

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable reatraining
systemctl restart reatraining

# 8) nginx-Site konfigurieren
cat > /etc/nginx/sites-available/reatraining <<'EOF'
server {
    listen 80;
    server_name _;  # <— hier Domain eintragen

    location /static/ {
        alias /var/www/reatraining/static/;
    }

    location / {
        include proxy_params;
        proxy_pass http://unix:/var/www/reatraining/reatraining.sock;
    }
}
EOF

ln -sf /etc/nginx/sites-available/reatraining /etc/nginx/sites-enabled/
nginx -t
systemctl reload nginx

echo "✅ Installation abgeschlossen!"
