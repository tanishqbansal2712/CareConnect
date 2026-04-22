from celery import Celery
from celery.schedules import crontab

def make_celery(app):
    celery = Celery(
        app.import_name,
        broker="redis://localhost:6379/0",
        backend="redis://localhost:6379/0",
    )

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

    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    celery.Task = ContextTask
    return celery