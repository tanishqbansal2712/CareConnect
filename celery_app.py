# celery_app.py
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask
from config import Config
from extensions import db, jwt, cache, mail
from flask_cors import CORS

# ── Build a minimal Flask app for Celery context ───────────────────────────────
def create_app():
    application = Flask(__name__)
    application.config.from_object(Config)
    CORS(application)
    db.init_app(application)
    jwt.init_app(application)
    cache.init_app(application)
    mail.init_app(application)
    return application

app = create_app()

# ── Create Celery instance ─────────────────────────────────────────────────────
from celery import Celery
from celery.schedules import crontab

celery = Celery(
    "careconnect",
    broker="redis://localhost:6379/0",
    backend="redis://localhost:6379/0",
)
celery.conf.update(app.config)

celery.conf.beat_schedule = {
    "daily-reminders": {
        "task":     "celery_app.send_daily_reminders",
        "schedule": crontab(hour=8, minute=0),
    },
    "monthly-doctor-report": {
        "task":     "celery_app.send_monthly_reports",
        "schedule": crontab(day_of_month=1, hour=7, minute=0),
    },
}
celery.conf.timezone = "Asia/Kolkata"

# make every task run inside Flask app context
class ContextTask(celery.Task):
    def __call__(self, *args, **kwargs):
        with app.app_context():
            return self.run(*args, **kwargs)

celery.Task = ContextTask

# ── Register tasks ─────────────────────────────────────────────────────────────

@celery.task(name="celery_app.send_daily_reminders")
def send_daily_reminders():
    from tasks.reminders import send_daily_reminders as _run
    with app.app_context():
        _run()


@celery.task(name="celery_app.send_monthly_reports")
def send_monthly_reports():
    from tasks.reports import send_monthly_reports as _run
    with app.app_context():
        _run()


@celery.task(name="celery_app.export_patient_csv", bind=True)
def export_patient_csv(self, patient_id):
    from tasks.exports import export_patient_csv as _run
    with app.app_context():
        return _run(patient_id)