#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
app.py

Flask-WebApp für Telefonreanimation QM-Training mit
- Login/Logout
- Training (Live-Stoppuhr & QM-Maßnahmen)
- Nacherfassung (manuelle Eingabe & QM-Auswertung, in Sessions gespeichert)
- Speicherung + Löschung von Sessions
- Auswertung (Tabellen, Diagramme, Punkte, Bestehen)
- PDF-Export (inkl. Feedback und Logo)
- Feedback-Gespräch (SBI + SMART)
- SQLite-Datenbank via SQLAlchemy
- Flask-Login
- Punktesystem: 46 Punkte, 35 zum Bestehen
"""

import os
import datetime

# dotenv laden, damit os.getenv() aus .env funktioniert
from dotenv import load_dotenv
basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))

from flask import (
    Flask, render_template, redirect, url_for,
    request, flash, jsonify, make_response
)
from flask_sqlalchemy import SQLAlchemy
from flask_login import (
    LoginManager, UserMixin, login_user,
    login_required, logout_user, current_user
)
from werkzeug.security import generate_password_hash, check_password_hash
import pdfkit  # pip install pdfkit; apt install wkhtmltopdf

# --- App & Config ---
app = Flask(__name__)

# Secrets und Verbindungen aus .env
app.config["SECRET_KEY"] = os.getenv("FLASK_SECRET_KEY")
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Pfad zur wkhtmltopdf-Binary
WKHTMLTOPDF_BIN = os.getenv("WKHTMLTOPDF_PATH", "/usr/bin/wkhtmltopdf")

db    = SQLAlchemy(app)
login = LoginManager(app)
login.login_view = "login"

# --- Thresholds, Punkte, QM-Schritte ---
THRESHOLDS = {
    ("Start", "Anrufannahme"): 10,
    ("Anrufannahme", "Erkennen Bewusstloser Patient"): 60,
    ("Erkennen Bewusstloser Patient", "Alarmieren der Rettungsmittel (Rapid Dispatch)"): 70,
    ("Alarmieren der Rettungsmittel (Rapid Dispatch)", "Erkennen Reanimationspflichtiger Patient"): 120,
    ("Erkennen Reanimationspflichtiger Patient", "Assistenz anfordern (Optional)"): 130,
    ("Assistenz anfordern (Optional)", "Kommunikation mit Rettungsmitteln (Optional durch Disponent 2)"): 210,
    ("Kommunikation mit Rettungsmitteln (Optional durch Disponent 2)", "Anleitung Reanimation eigenständig"): 200,
    ("Anleitung Reanimation eigenständig", "Anleitung Reanimation durch CSNA"): 200,
    ("Anleitung Reanimation durch CSNA", "Metronom"): 245,
    ("Metronom", "Rückversichern der Geschwindigkeit und Drucktiefe"): 280
}

POINTS = {
    "Anrufannahme": 2,
    "Erkennen Bewusstloser Patient": 5,
    "Alarmieren der Rettungsmittel (Rapid Dispatch)": 5,
    "Erkennen Reanimationspflichtiger Patient": 5,
    "Assistenz anfordern (Optional)": 2,
    "Kommunikation mit Rettungsmitteln (Optional durch Disponent 2)": 3,
    "Anleitung Reanimation eigenständig": 5,
    "Anleitung Reanimation durch CSNA": 10,
    "Metronom": 1,
    "Rückversichern der Geschwindigkeit und Drucktiefe": 3
}

MAX_POINTS     = sum(POINTS.values())  # 46
PASS_THRESHOLD = 35

QM_TASKS = [
    "Anrufannahme",
    "Erkennen Bewusstloser Patient",
    "Alarmieren der Rettungsmittel (Rapid Dispatch)",
    "Erkennen Reanimationspflichtiger Patient",
    "Assistenz anfordern (Optional)",
    "Kommunikation mit Rettungsmitteln (Optional durch Disponent 2)",
    "Anleitung Reanimation eigenständig",
    "Anleitung Reanimation durch CSNA",
    "Metronom",
    "Rückversichern der Geschwindigkeit und Drucktiefe"
]

# --- Models ---
class User(UserMixin, db.Model):
    id       = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    pw_hash  = db.Column(db.String(128), nullable=False)
    def set_password(self, pw):   self.pw_hash = generate_password_hash(pw)
    def check_password(self, pw): return check_password_hash(self.pw_hash, pw)

class Session(db.Model):
    id         = db.Column(db.Integer, primary_key=True)
    trainer    = db.Column(db.String(64), nullable=False)
    disponent  = db.Column(db.String(64), nullable=False)
    start_time = db.Column(db.DateTime, nullable=False)
    end_time   = db.Column(db.DateTime, nullable=True)
    total_sec  = db.Column(db.Integer, nullable=True)
    steps      = db.relationship("Step", backref="session", cascade="all, delete-orphan")
    feedbacks  = db.relationship("Feedback", backref="session", cascade="all, delete-orphan")

class Step(db.Model):
    id           = db.Column(db.Integer, primary_key=True)
    session_id   = db.Column(db.Integer, db.ForeignKey("session.id"), nullable=False)
    name         = db.Column(db.String(128), nullable=False)
    cumulative   = db.Column(db.Integer, nullable=True)
    interval     = db.Column(db.Integer, nullable=True)
    out_of_order = db.Column(db.Boolean, default=False)

class Feedback(db.Model):
    id             = db.Column(db.Integer, primary_key=True)
    session_id     = db.Column(db.Integer, db.ForeignKey("session.id"), nullable=False)
    timestamp      = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    pos_situation  = db.Column(db.Text, nullable=False)
    pos_behavior   = db.Column(db.Text, nullable=False)
    pos_impact     = db.Column(db.Text, nullable=False)
    neg_situation  = db.Column(db.Text, nullable=False)
    neg_behavior   = db.Column(db.Text, nullable=False)
    neg_impact     = db.Column(db.Text, nullable=False)
    smart_goal     = db.Column(db.Text, nullable=False)
    support        = db.Column(db.Text, nullable=False)
    next_steps     = db.Column(db.Text, nullable=False)
    overall        = db.Column(db.Text, nullable=False)

@login.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# --- Routes (unverändert) ---
@app.route("/")
def root():
    return redirect(url_for("training") if current_user.is_authenticated else url_for("login"))

@app.route("/login", methods=["GET","POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("training"))
    if request.method == "POST":
        u = User.query.filter_by(username=request.form["username"]).first()
        if u and u.check_password(request.form["password"]):
            login_user(u)
            return redirect(url_for("training"))
        flash("Ungültige Zugangsdaten", "danger")
    return render_template("login.html")

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))

@app.route("/training")
@login_required
def training():
    return render_template("training.html", QM_TASKS=QM_TASKS)

@app.route("/submit", methods=["POST"])
@login_required
def submit():
    data = request.get_json()
    sess = Session(
        trainer    = current_user.username,
        disponent  = data["disponent"],
        start_time = datetime.datetime.fromisoformat(data["start"]),
        end_time   = datetime.datetime.fromisoformat(data["end"]),
        total_sec  = data["total"]
    )
    db.session.add(sess)
    db.session.flush()
    for st in data["steps"]:
        db.session.add(Step(
            session_id   = sess.id,
            name         = st["name"],
            cumulative   = st["cumulative"],
            interval     = st["interval"],
            out_of_order = st.get("outOfOrder", False)
        ))
    db.session.commit()
    return jsonify(success=True)

@app.route("/nacherfassung", methods=["GET","POST"])
@login_required
def nacherfassung():
    if request.method == "POST":
        disponent = request.form.get("disponent","").strip()
        # 1) Werte lesen
        values = []
        for step in QM_TASKS:
            key = f"time_{step}"
            try:    cum = int(request.form.get(key,"0"))
            except: cum = None
            values.append((step, cum))
        # 2) Auswertung
        prev, total, pts = 0, 0, 0
        steps = []
        for name, cum in values:
            thr = next((t for (a,b),t in THRESHOLDS.items() if b==name), None)
            if cum is None:
                interval, status = None, "Fehlt"
            else:
                interval = cum - prev
                prev, total = cum, cum
                status = "OK" if thr is None or cum<=thr else "Zu langsam"
                full = POINTS.get(name,0)
                if status=="OK":
                    over = max(cum-(thr or 0),0)
                    ded  = int((over/thr)//0.1) if thr else 0
                    pts += max(full-ded, full)
            steps.append({
                "name":       name,
                "cumulative": cum,
                "interval":   interval,
                "threshold":  thr,
                "status":     status
            })
        passed = (pts>=PASS_THRESHOLD)
        # 3) als Session speichern
        now = datetime.datetime.utcnow()
        sess = Session(
            trainer    = current_user.username,
            disponent  = disponent,
            start_time = now,
            end_time   = now+datetime.timedelta(seconds=total),
            total_sec  = total
        )
        db.session.add(sess)
        db.session.flush()
        for s in steps:
            db.session.add(Step(
                session_id   = sess.id,
                name         = s["name"],
                cumulative   = s["cumulative"],
                interval     = s["interval"],
                out_of_order = False
            ))
        db.session.commit()
        return redirect(url_for("results"))
    return render_template("nacherfassung.html", QM_TASKS=QM_TASKS)

@app.route("/delete/<int:session_id>", methods=["POST"])
@login_required
def delete_session(session_id):
    s = Session.query.get_or_404(session_id)
    db.session.delete(s)
    db.session.commit()
    flash("Eintrag gelöscht.", "info")
    return redirect(url_for("results"))

@app.route("/results")
@login_required
def results():
    sessions_list = []
    for s in Session.query.order_by(Session.start_time.desc()).all():
        steps, pts = [], 0
        for st in s.steps:
            thr    = next((t for (a,b),t in THRESHOLDS.items() if b==st.name), 0)
            actual = st.cumulative or 0
            status = "OK" if actual<=thr else "Zu langsam"
            full   = POINTS.get(st.name,0)
            if status=="OK":
                over = max(actual-thr,0)
                ded  = int((over/thr)//0.1) if thr else 0
                pts += max(full-ded, full)
            steps.append({
                "name":       st.name,
                "cumulative": actual,
                "threshold":  thr,
                "status":     status
            })
        passed = (pts>=PASS_THRESHOLD)
        sessions_list.append({
            "id":        s.id,
            "trainer":   s.trainer,
            "disponent": s.disponent,
            "start":     s.start_time.isoformat(),
            "total":     s.total_sec,
            "steps":     steps,
            "score":     pts,
            "passed":    passed,
            "fb_count":  len(s.feedbacks)
        })
    return render_template(
        "results.html",
        sessions       = sessions_list,
        total_sessions = len(sessions_list),
        avg_total      = int(sum(x["total"] for x in sessions_list)/len(sessions_list)) if sessions_list else 0,
        avg_score      = int(sum(x["score"] for x in sessions_list)/len(sessions_list)) if sessions_list else 0,
        max_points     = MAX_POINTS,
        pass_threshold = PASS_THRESHOLD
    )

@app.route("/report/pdf/<int:session_id>")
@login_required
def pdf_report(session_id):
    s = Session.query.get_or_404(session_id)
    steps, pts = [], 0
    for st in s.steps:
        thr    = next((t for (a,b),t in THRESHOLDS.items() if b==st.name), 0)
        actual = st.cumulative or 0
        status = "OK" if actual<=thr else "Zu langsam"
        full   = POINTS.get(st.name,0)
        if status=="OK":
            over = max(actual-thr,0)
            ded  = int((over/thr)//0.1) if thr else 0
            pts += max(full-ded, full)
        steps.append({
            "name":       st.name,
            "cumulative": actual,
            "threshold":  thr,
            "status":     status
        })
    passed = (pts>=PASS_THRESHOLD)
    feedbacks = [{
        "timestamp":     fb.timestamp.strftime("%Y-%m-%d %H:%M"),
        "pos_situation": fb.pos_situation,
        "pos_behavior":  fb.pos_behavior,
        "pos_impact":    fb.pos_impact,
        "neg_situation": fb.neg_situation,
        "neg_behavior":  fb.neg_behavior,
        "neg_impact":    fb.neg_impact,
        "smart_goal":    fb.smart_goal,
        "support":       fb.support,
        "next_steps":    fb.next_steps,
        "overall":       fb.overall
    } for fb in s.feedbacks]

    rendered = render_template(
        "pdf_report.html",
        session       = s,
        steps         = steps,
        score         = pts,
        passed        = passed,
        max_points    = MAX_POINTS,
        pass_threshold= PASS_THRESHOLD,
        feedbacks     = feedbacks
    )
    # PDF-Generierung mit lokalem Dateizugriff für das SVG-Logo
    config  = pdfkit.configuration(wkhtmltopdf=WKHTMLTOPDF_BIN)
    options = {'enable-local-file-access': None}
    try:
        pdf = pdfkit.from_string(rendered, False, configuration=config, options=options)
    except Exception as e:
        flash(f"PDF-Generierung fehlgeschlagen: {e}", "danger")
        return redirect(url_for("results"))

    resp = make_response(pdf)
    resp.headers["Content-Type"]        = "application/pdf"
    resp.headers["Content-Disposition"] = f"attachment; filename=report_{session_id}.pdf"
    return resp

@app.route("/feedback/<int:session_id>", methods=["GET","POST"])
@login_required
def feedback(session_id):
    s = Session.query.get_or_404(session_id)
    if request.method == "POST":
        fb = Feedback(
            session_id     = session_id,
            pos_situation  = request.form["pos_situation"],
            pos_behavior   = request.form["pos_behavior"],
            pos_impact     = request.form["pos_impact"],
            neg_situation  = request.form["neg_situation"],
            neg_behavior   = request.form["neg_behavior"],
            neg_impact     = request.form["neg_impact"],
            smart_goal     = request.form["smart_goal"],
            support        = request.form["support"],
            next_steps     = request.form["next_steps"],
            overall        = request.form["overall"]
        )
        db.session.add(fb)
        db.session.commit()
        flash("Feedback gespeichert.", "success")
        return redirect(url_for("feedback", session_id=session_id))
    return render_template("feedback.html", session=s)

@app.route("/feedback-guide")
@login_required
def guidance():
    return render_template("guidance.html")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
