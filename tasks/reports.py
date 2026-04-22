
# Job b — Monthly activity report sent to every doctor on the 1st of each month.

from extensions import mail
from flask_mail import Message
from datetime import date
from calendar import monthrange


def send_monthly_reports():
    """
    Scheduled task: runs on the 1st of every month at 7 AM.
    For each doctor, generates an HTML report of the previous
    month's activity and sends it via email.
    """
    from models import Doctor, Appointment, Treatment
    from app import app

    with app.app_context():
        today = date.today()

        # calculate previous month range
        if today.month == 1:
            year, month = today.year - 1, 12
        else:
            year, month = today.year, today.month - 1

        month_start = date(year, month, 1)
        month_end   = date(year, month, monthrange(year, month)[1])
        month_label = month_start.strftime("%B %Y")

        doctors = Doctor.query.all()
        sent = 0

        for doctor in doctors:
            if not doctor.user or not doctor.user.email:
                continue

            appointments = Appointment.query.filter_by(
                doctor_id=doctor.id
            ).filter(
                Appointment.date >= month_start,
                Appointment.date <= month_end
            ).order_by(Appointment.date).all()

            try:
                msg = Message(
                    subject  = f"CareConnect — Monthly Report: {month_label}",
                    recipients = [doctor.user.email],
                    html     = _report_html(doctor.name, month_label, appointments)
                )
                mail.send(msg)
                sent += 1
            except Exception as e:
                print(f"[Reports] Failed for Dr.{doctor.name}: {e}")

        print(f"[Reports] Sent {sent} monthly report(s) for {month_label}.")


def _report_html(doctor_name, month_label, appointments):
    total      = len(appointments)
    completed  = sum(1 for a in appointments if a.status == "completed")
    cancelled  = sum(1 for a in appointments if a.status == "cancelled")
    booked     = sum(1 for a in appointments if a.status == "booked")

    # build appointment rows
    rows = ""
    for a in appointments:
        t = a.treatment
        bg = {
            "completed": "#e8f5e9",
            "cancelled":  "#fce4ec",
            "booked":     "#fff8e1",
        }.get(a.status, "white")

        rows += f"""
        <tr style="background:{bg}">
          <td style="padding:10px;border-bottom:1px solid #eee">{a.id}</td>
          <td style="padding:10px;border-bottom:1px solid #eee">{a.patient.name}</td>
          <td style="padding:10px;border-bottom:1px solid #eee">{a.date}</td>
          <td style="padding:10px;border-bottom:1px solid #eee">{str(a.time)[:5]}</td>
          <td style="padding:10px;border-bottom:1px solid #eee">{a.status.capitalize()}</td>
          <td style="padding:10px;border-bottom:1px solid #eee">{t.diagnosis    if t else '—'}</td>
          <td style="padding:10px;border-bottom:1px solid #eee">{t.prescription if t else '—'}</td>
        </tr>
        """

    if not rows:
        rows = """<tr><td colspan="7" style="text-align:center;padding:20px;color:#888">
                  No appointments this month.</td></tr>"""

    return f"""
    <div style="font-family:Segoe UI,sans-serif;max-width:900px;margin:auto">

      <!-- Header -->
      <div style="background:linear-gradient(90deg,#0f2027,#2c5364);
                  padding:28px;border-radius:12px 12px 0 0;text-align:center">
        <h2 style="color:white;margin:0">🏥 CareConnect</h2>
        <p style="color:rgba(255,255,255,0.8);margin:6px 0 0">
          Monthly Activity Report — {month_label}
        </p>
      </div>

      <!-- Summary cards -->
      <div style="display:flex;gap:16px;padding:24px;background:#f4f6f9">
        {_stat_card("Total", total,     "#004e92")}
        {_stat_card("Completed", completed, "#198754")}
        {_stat_card("Cancelled", cancelled, "#dc3545")}
        {_stat_card("Booked",    booked,    "#fd7e14")}
      </div>

      <!-- Greeting -->
      <div style="padding:0 24px 16px;background:#f4f6f9">
        <p style="color:#333">Dear <b>Dr. {doctor_name}</b>,</p>
        <p style="color:#555;line-height:1.7">
          Here is your activity summary for <b>{month_label}</b>.
          Please find the detailed appointment breakdown below.
        </p>
      </div>

      <!-- Table -->
      <div style="padding:0 24px 32px;background:#f4f6f9">
        <table style="width:100%;border-collapse:collapse;background:white;
                      border-radius:10px;overflow:hidden;
                      box-shadow:0 2px 8px rgba(0,0,0,0.08)">
          <thead>
            <tr style="background:linear-gradient(135deg,#000428,#004e92);color:white">
              <th style="padding:12px;text-align:left">#</th>
              <th style="padding:12px;text-align:left">Patient</th>
              <th style="padding:12px;text-align:left">Date</th>
              <th style="padding:12px;text-align:left">Time</th>
              <th style="padding:12px;text-align:left">Status</th>
              <th style="padding:12px;text-align:left">Diagnosis</th>
              <th style="padding:12px;text-align:left">Prescription</th>
            </tr>
          </thead>
          <tbody>{rows}</tbody>
        </table>
      </div>

      <!-- Footer -->
      <div style="background:#2c5364;padding:16px;text-align:center;
                  border-radius:0 0 12px 12px">
        <p style="color:rgba(255,255,255,0.7);margin:0;font-size:13px">
          © 2025 CareConnect Hospital Management System
        </p>
      </div>
    </div>
    """


def _stat_card(label, value, color):
    return f"""
    <div style="flex:1;background:white;border-radius:10px;padding:16px;
                text-align:center;box-shadow:0 2px 6px rgba(0,0,0,0.08)">
      <h3 style="color:{color};margin:0;font-size:28px">{value}</h3>
      <p style="color:#666;margin:4px 0 0;font-size:13px">{label}</p>
    </div>
    """