
# Job c — Async CSV export triggered by the patient from their dashboard.
import csv
import os
from datetime import datetime


def export_patient_csv(patient_id):
    """
    Async Celery task triggered by patient.
    Generates a CSV of all treatment history for the patient
    and sends it to their email as an attachment.
    """
    from models import Patient, Appointment
    from extensions import mail
    from flask_mail import Message, Attachment
    from app import app

    with app.app_context():
        patient = Patient.query.get(patient_id)
        if not patient:
            print(f"[Export] Patient {patient_id} not found.")
            return "patient_not_found"

        appointments = Appointment.query.filter_by(
            patient_id=patient_id
        ).order_by(Appointment.date.desc()).all()

        # ── Build CSV in memory ────────────────────────────────
        export_dir = os.path.join(os.getcwd(), "exports")
        os.makedirs(export_dir, exist_ok=True)

        timestamp  = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename   = f"treatment_history_{patient.name.replace(' ','_')}_{timestamp}.csv"
        filepath   = os.path.join(export_dir, filename)

        with open(filepath, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)

            # header row
            writer.writerow([
                "User ID", "Username", "Patient Name",
                "Consulting Doctor", "Doctor Specialization",
                "Appointment Date", "Appointment Time", "Status",
                "Diagnosis", "Prescription", "Doctor Notes", "Next Visit"
            ])

            # data rows
            for appt in appointments:
                t = appt.treatment
                writer.writerow([
                    patient.user_id,
                    patient.user.username,
                    patient.name,
                    appt.doctor.name,
                    appt.doctor.specialization,
                    str(appt.date),
                    str(appt.time)[:5],
                    appt.status,
                    t.diagnosis      if t else "",
                    t.prescription   if t else "",
                    t.notes          if t else "",
                    str(t.next_visit) if t and t.next_visit else "",
                ])

        # ── Send email with CSV attached ───────────────────────
        try:
            with open(filepath, "rb") as f:
                csv_data = f.read()

            msg = Message(
                subject    = "CareConnect — Your Treatment History Export 📋",
                recipients = [patient.email],
                html       = _export_done_html(patient.name, filename),
                attachments = [
                    Attachment(
                        filename     = filename,
                        content_type = "text/csv",
                        data         = csv_data,
                    )
                ]
            )
            mail.send(msg)
            print(f"[Export] CSV sent to {patient.email}")
        except Exception as e:
            print(f"[Export] Email failed for patient {patient_id}: {e}")

        return filepath


def _export_done_html(patient_name, filename):
    return f"""
    <div style="font-family:Segoe UI,sans-serif;max-width:520px;margin:auto;
                border-radius:12px;overflow:hidden;box-shadow:0 4px 12px rgba(0,0,0,0.1)">

      <div style="background:linear-gradient(90deg,#0f2027,#2c5364);
                  padding:24px;text-align:center">
        <h2 style="color:white;margin:0">🏥 CareConnect</h2>
        <p style="color:rgba(255,255,255,0.8);margin:6px 0 0">Treatment History Export</p>
      </div>

      <div style="padding:32px;background:white">
        <p style="font-size:16px">Dear <b>{patient_name}</b>,</p>
        <p style="color:#444;line-height:1.7">
          Your treatment history export is ready!
          The file <b>{filename}</b> is attached to this email.
        </p>
        <div style="background:#e8f5e9;border-left:4px solid #198754;
                    border-radius:8px;padding:16px;margin:20px 0">
          <p style="margin:0;color:#155724">
            ✅ Export completed successfully. Please find the CSV attached.
          </p>
        </div>
        <p style="color:#888;font-size:13px;margin-top:24px">
          — CareConnect Hospital Management System
        </p>
      </div>
    </div>
    """