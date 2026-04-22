from flask import Blueprint, jsonify, request
from models import Appointment, Treatment, Doctor, Patient, DoctorAvailability
from extensions import db
from datetime import date, timedelta

doctor_bp = Blueprint("doctor", __name__, url_prefix="/doctor")


# ── DASHBOARD DATA ─────────────────────────────────────────────────────────────
@doctor_bp.route("/dashboard_data/<int:doc_id>")
def dashboard_data(doc_id):
    doctor = Doctor.query.get_or_404(doc_id)
    today  = date.today()
    week_end = today + timedelta(days=7)

    today_appts = Appointment.query.filter_by(doctor_id=doc_id)\
        .filter(Appointment.date == today)\
        .filter(Appointment.status == "booked").all()

    week_appts = Appointment.query.filter_by(doctor_id=doc_id)\
        .filter(Appointment.date > today)\
        .filter(Appointment.date <= week_end)\
        .filter(Appointment.status == "booked").all()

    # unique patients assigned to this doctor
    all_appts = Appointment.query.filter_by(doctor_id=doc_id).all()
    seen = set()
    patients = []
    for a in all_appts:
        if a.patient_id not in seen:
            seen.add(a.patient_id)
            patients.append({"id": a.patient.id, "name": a.patient.name, "email": a.patient.email})

    stats = [
        {"label": "Today's Appointments", "value": len(today_appts)},
        {"label": "This Week",            "value": len(week_appts)},
        {"label": "Total Patients",       "value": len(patients)},
    ]

    def fmt(a):
        return {
            "id":      a.id,
            "patient": a.patient.name,
            "patient_id": a.patient_id,
            "date":    str(a.date),
            "time":    str(a.time),
            "status":  a.status,
            "reason":  a.reason or "",
        }

    return jsonify({
        "stats":        stats,
        "today":        [fmt(a) for a in today_appts],
        "week":         [fmt(a) for a in week_appts],
        "patients":     patients,
        "doctor_name":  doctor.name,
    })


# ── ALL APPOINTMENTS FOR A DOCTOR ──────────────────────────────────────────────
@doctor_bp.route("/appointments/<int:doc_id>")
def get_appointments(doc_id):
    appointments = Appointment.query.filter_by(doctor_id=doc_id)\
        .order_by(Appointment.date.desc()).all()
    return jsonify([{
        "id":         a.id,
        "patient":    a.patient.name,
        "patient_id": a.patient_id,
        "date":       str(a.date),
        "time":       str(a.time),
        "status":     a.status,
        "reason":     a.reason or "",
    } for a in appointments])


# ── MARK COMPLETE + ADD TREATMENT ─────────────────────────────────────────────
@doctor_bp.route("/complete/<int:appointment_id>", methods=["POST"])
def complete_appointment(appointment_id):
    appointment = Appointment.query.get_or_404(appointment_id)
    data = request.json

    if not data.get("diagnosis"):
        return jsonify({"msg": "Diagnosis is required"}), 400

    appointment.status = "completed"

    # update existing treatment or create new
    if appointment.treatment:
        appointment.treatment.diagnosis   = data["diagnosis"]
        appointment.treatment.prescription = data.get("prescription", "")
        appointment.treatment.notes        = data.get("notes", "")
    else:
        treatment = Treatment(
            appointment_id = appointment_id,
            diagnosis      = data["diagnosis"],
            prescription   = data.get("prescription", ""),
            notes          = data.get("notes", ""),
        )
        db.session.add(treatment)

    db.session.commit()
    return jsonify({"msg": "Appointment completed and treatment saved"})


# ── CANCEL APPOINTMENT ─────────────────────────────────────────────────────────
@doctor_bp.route("/cancel/<int:appointment_id>", methods=["POST"])
def cancel_appointment(appointment_id):
    appointment = Appointment.query.get_or_404(appointment_id)
    appointment.status = "cancelled"
    db.session.commit()
    return jsonify({"msg": "Appointment cancelled"})


# ── PATIENT HISTORY (for doctor view) ─────────────────────────────────────────
@doctor_bp.route("/patient_history/<int:patient_id>")
def patient_history(patient_id):
    appointments = Appointment.query.filter_by(patient_id=patient_id)\
        .order_by(Appointment.date.desc()).all()
    history = []
    for a in appointments:
        t = a.treatment
        history.append({
            "appointment_id": a.id,
            "date":           str(a.date),
            "time":           str(a.time),
            "status":         a.status,
            "reason":         a.reason or "",
            "diagnosis":      t.diagnosis    if t else None,
            "prescription":   t.prescription if t else None,
            "notes":          t.notes        if t else None,
        })
    return jsonify(history)


# ── SET AVAILABILITY (next 7 days) ────────────────────────────────────────────
@doctor_bp.route("/availability", methods=["POST"])
def set_availability():
    data      = request.json
    doc_id    = data.get("doctor_id")
    slots     = data.get("slots", [])
    today     = date.today()
    max_date  = today + timedelta(days=7)

    if not doc_id or not slots:
        return jsonify({"msg": "doctor_id and slots are required"}), 400

    added = 0
    for slot in slots:
        try:
            from datetime import datetime
            slot_date  = datetime.strptime(slot["date"],  "%Y-%m-%d").date()
            start_time = datetime.strptime(slot["start"], "%H:%M").time()
            end_time   = datetime.strptime(slot["end"],   "%H:%M").time()
        except (KeyError, ValueError):
            continue

        # only allow dates within next 7 days
        if not (today <= slot_date <= max_date):
            continue

        # skip if slot already exists
        exists = DoctorAvailability.query.filter_by(
            doctor_id=doc_id, avail_date=slot_date, start_time=start_time
        ).first()
        if exists:
            continue

        db.session.add(DoctorAvailability(
            doctor_id  = doc_id,
            avail_date = slot_date,
            start_time = start_time,
            end_time   = end_time,
        ))
        added += 1

    db.session.commit()
    return jsonify({"msg": f"{added} slot(s) saved"})


# ── GET AVAILABILITY ──────────────────────────────────────────────────────────
@doctor_bp.route("/availability/<int:doc_id>")
def get_availability(doc_id):
    today    = date.today()
    max_date = today + timedelta(days=7)
    slots = DoctorAvailability.query.filter_by(doctor_id=doc_id)\
        .filter(DoctorAvailability.avail_date >= today)\
        .filter(DoctorAvailability.avail_date <= max_date)\
        .order_by(DoctorAvailability.avail_date, DoctorAvailability.start_time).all()
    return jsonify([{
        "id":        s.id,
        "date":      str(s.avail_date),
        "start":     str(s.start_time)[:5],
        "end":       str(s.end_time)[:5],
        "is_booked": s.is_booked,
    } for s in slots])