from flask import Blueprint, request, jsonify
from models import Appointment, Doctor, DoctorAvailability, Treatment, Patient, Department, User
from extensions import db, cache
from datetime import date, timedelta, datetime

patient_bp = Blueprint("patient", __name__, url_prefix="/patient")


# ── DASHBOARD DATA ─────────────────────────────────────────────────────────────
@patient_bp.route("/dashboard_data/<int:patient_id>")
def dashboard_data(patient_id):
    patient = Patient.query.get_or_404(patient_id)
    today   = date.today()

    # upcoming appointments (booked, date >= today)
    upcoming = Appointment.query.filter_by(patient_id=patient_id)\
        .filter(Appointment.status == "booked")\
        .filter(Appointment.date >= today)\
        .order_by(Appointment.date, Appointment.time).all()

    # past appointments (completed or cancelled)
    past = Appointment.query.filter_by(patient_id=patient_id)\
        .filter(Appointment.status != "booked")\
        .order_by(Appointment.date.desc()).all()

    stats = [
        {"label": "Upcoming Appointments", "value": len(upcoming)},
        {"label": "Past Appointments",     "value": len(past)},
        {"label": "Total Appointments",    "value": len(upcoming) + len(past)},
    ]

    def fmt_upcoming(a):
        return {
            "id":     a.id,
            "doctor": a.doctor.name,
            "spec":   a.doctor.specialization,
            "date":   str(a.date),
            "time":   str(a.time)[:5],
            "status": a.status,
            "reason": a.reason or "",
        }

    def fmt_past(a):
        t = a.treatment
        return {
            "id":           a.id,
            "doctor":       a.doctor.name,
            "spec":         a.doctor.specialization,
            "date":         str(a.date),
            "time":         str(a.time)[:5],
            "status":       a.status,
            "diagnosis":    t.diagnosis    if t else None,
            "prescription": t.prescription if t else None,
            "notes":        t.notes        if t else None,
            "next_visit":   str(t.next_visit) if t and t.next_visit else None,
        }

    return jsonify({
        "stats":    stats,
        "upcoming": [fmt_upcoming(a) for a in upcoming],
        "past":     [fmt_past(a)     for a in past],
        "patient":  {
            "id":      patient.id,
            "name":    patient.name,
            "email":   patient.email,
            "phone":   patient.phone  or "",
            "address": patient.address or "",
        }
    })


# ── ALL DEPARTMENTS ────────────────────────────────────────────────────────────
@patient_bp.route("/departments")
@cache.cached(timeout=600, key_prefix='departments')
def get_departments():
    depts = Department.query.all()
    return jsonify([
        {"id": d.id, "name": d.name, "description": d.description,
         "doctor_count": len([doc for doc in d.doctors if doc.user and doc.user.is_active])}
        for d in depts
    ])


# ── DOCTORS LIST (with 7-day availability) ────────────────────────────────────
@patient_bp.route("/doctors")
def get_doctors():
    today    = date.today()
    max_date = today + timedelta(days=7)

    # optional filter by specialization
    spec = request.args.get("specialization", "").strip()
    query = Doctor.query.join(User).filter(User.is_active == True)
    if spec:
        query = query.filter(Doctor.specialization.ilike(f"%{spec}%"))

    doctors = query.all()
    result  = []
    for d in doctors:
        slots = DoctorAvailability.query.filter_by(doctor_id=d.id, is_booked=False)\
            .filter(DoctorAvailability.avail_date >= today)\
            .filter(DoctorAvailability.avail_date <= max_date)\
            .order_by(DoctorAvailability.avail_date, DoctorAvailability.start_time).all()

        result.append({
            "id":             d.id,
            "name":           d.name,
            "specialization": d.specialization,
            "phone":          d.phone or "",
            "department":     d.department.name if d.department else "",
            "availability": [
                {
                    "slot_id": s.id,
                    "date":    str(s.avail_date),
                    "start":   str(s.start_time)[:5],
                    "end":     str(s.end_time)[:5],
                }
                for s in slots
            ]
        })
    return jsonify(result)


# ── BOOK APPOINTMENT ──────────────────────────────────────────────────────────
@patient_bp.route("/book", methods=["POST"])
def book_appointment():
    data = request.json

    required = ["patient_id", "doctor_id", "date", "time"]
    if not all(data.get(k) for k in required):
        return jsonify({"msg": "patient_id, doctor_id, date and time are required"}), 400

    try:
        appt_date = datetime.strptime(data["date"], "%Y-%m-%d").date()
        appt_time = datetime.strptime(data["time"], "%H:%M").time()
    except ValueError:
        return jsonify({"msg": "date must be YYYY-MM-DD and time HH:MM"}), 400

    # prevent double booking
    existing = Appointment.query.filter_by(
        doctor_id=data["doctor_id"],
        date=appt_date,
        time=appt_time
    ).first()
    if existing:
        return jsonify({"msg": "This slot is already booked"}), 409

    appointment = Appointment(
        patient_id = data["patient_id"],
        doctor_id  = data["doctor_id"],
        date       = appt_date,
        time       = appt_time,
        status     = "booked",
        reason     = data.get("reason", ""),
    )
    db.session.add(appointment)

    # mark the availability slot as booked if it exists
    if data.get("slot_id"):
        slot = DoctorAvailability.query.get(data["slot_id"])
        if slot:
            slot.is_booked = True

    db.session.commit()
    return jsonify({"msg": "Appointment booked successfully", "id": appointment.id}), 201


# ── CANCEL APPOINTMENT ────────────────────────────────────────────────────────
@patient_bp.route("/cancel/<int:appointment_id>", methods=["POST"])
def cancel_appointment(appointment_id):
    appointment = Appointment.query.get_or_404(appointment_id)

    if appointment.status != "booked":
        return jsonify({"msg": "Only booked appointments can be cancelled"}), 400

    appointment.status = "cancelled"

    # free the availability slot back
    slot = DoctorAvailability.query.filter_by(
        doctor_id  = appointment.doctor_id,
        avail_date = appointment.date,
        start_time = appointment.time,
    ).first()
    if slot:
        slot.is_booked = False

    db.session.commit()
    return jsonify({"msg": "Appointment cancelled"})


# ── EDIT PATIENT PROFILE ──────────────────────────────────────────────────────
@patient_bp.route("/profile/<int:patient_id>", methods=["PUT"])
def edit_profile(patient_id):
    patient = Patient.query.get_or_404(patient_id)
    data    = request.json

    patient.name    = data.get("name",    patient.name)
    patient.phone   = data.get("phone",   patient.phone)
    patient.address = data.get("address", patient.address)

    # also update email on User if changed
    if data.get("email") and data["email"] != patient.email:
        if User.query.filter_by(email=data["email"]).first():
            return jsonify({"msg": "Email already in use"}), 409
        patient.email      = data["email"]
        patient.user.email = data["email"]

    db.session.commit()
    return jsonify({"msg": "Profile updated successfully"})


# ── TREATMENT HISTORY ─────────────────────────────────────────────────────────
@patient_bp.route("/history/<int:patient_id>")
def get_history(patient_id):
    appointments = Appointment.query.filter_by(patient_id=patient_id)\
        .order_by(Appointment.date.desc()).all()
    history = []
    for a in appointments:
        t = a.treatment
        history.append({
            "appointment_id": a.id,
            "doctor":         a.doctor.name,
            "spec":           a.doctor.specialization,
            "date":           str(a.date),
            "time":           str(a.time)[:5],
            "status":         a.status,
            "diagnosis":      t.diagnosis    if t else None,
            "prescription":   t.prescription if t else None,
            "notes":          t.notes        if t else None,
            "next_visit":     str(t.next_visit) if t and t.next_visit else None,
        })
    return jsonify(history)


# ── SEARCH DOCTORS ────────────────────────────────────────────────────────────
@patient_bp.route("/search")
def search_doctors():
    q = request.args.get("q", "").strip()
    if not q:
        return jsonify([])
    doctors = Doctor.query.join(User).filter(User.is_active == True).filter(
        Doctor.name.ilike(f"%{q}%") | Doctor.specialization.ilike(f"%{q}%")
    ).all()
    return jsonify([
        {"id": d.id, "name": d.name, "specialization": d.specialization, "phone": d.phone or ""}
        for d in doctors
    ])