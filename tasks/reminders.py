
# Job a — Daily reminders sent every morning at 8 AM.

from extensions import mail
from flask_mail import Message
from datetime import date

def send_daily_reminders():
    """
    Scheduled task: runs every day at 8 AM.
    Finds all booked appointments for today and sends
    a reminder email to each patient.
    """
    # import here to avoid circular imports at module load
    from models import Appointment
    from app import app

    today = date.today()

    with app.app_context():
        appointments = Appointment.query.filter_by(
            status="booked"
        ).filter(Appointment.date == today).all()

        if not appointments:
            print(f"[Reminders] No appointments today ({today}). Nothing to send.")
            return

        sent = 0
        for appt in appointments:
            patient = appt.patient
            doctor  = appt.doctor

            if not patient or not patient.email:
                continue

            try:
                msg = Message(
                    subject = "CareConnect — Appointment Reminder 🏥",
                    recipients = [patient.email],
                    html = _reminder_html(patient.name, doctor.name,
                                          str(appt.date), str(appt.time)[:5])
                )
                mail.send(msg)
                sent += 1
            except Exception as e:
                print(f"[Reminders] Failed to send to {patient.email}: {e}")

        print(f"[Reminders] Sent {sent} reminder(s) for {today}.")


def _reminder_html(patient_name, doctor_name, appt_date, appt_time):
    return f"""
    <div style="font-family:Segoe UI,sans-serif;max-width:520px;margin:auto;
                border-radius:12px;overflow:hidden;box-shadow:0 4px 12px rgba(0,0,0,0.1)">

      <div style="background:linear-gradient(90deg,#0f2027,#2c5364);
                  padding:24px;text-align:center">
        <h2 style="color:white;margin:0">🏥 CareConnect</h2>
        <p style="color:rgba(255,255,255,0.8);margin:6px 0 0">Appointment Reminder</p>
      </div>

      <div style="padding:32px;background:white">
        <p style="font-size:16px">Dear <b>{patient_name}</b>,</p>
        <p style="color:#444;line-height:1.7">
          This is a friendly reminder that you have an appointment scheduled
          <b>today</b> at CareConnect Hospital.
        </p>

        <div style="background:#f0f4ff;border-left:4px solid #004e92;
                    border-radius:8px;padding:16px;margin:20px 0">
          <p style="margin:4px 0">🩺 <b>Doctor:</b> Dr. {doctor_name}</p>
          <p style="margin:4px 0">📅 <b>Date:</b> {appt_date}</p>
          <p style="margin:4px 0">🕐 <b>Time:</b> {appt_time}</p>
        </div>

        <p style="color:#444">
          Please arrive <b>10 minutes early</b> and carry any previous
          prescriptions or reports.
        </p>
        <p style="color:#888;font-size:13px;margin-top:24px">
          — CareConnect Hospital Management System
        </p>
      </div>
    </div>
    """