from flask import Blueprint, request, jsonify
from models import Doctor, Appointment, Patient, User, Department
from extensions import db

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


# ── DASHBOARD DATA ─────────────────────────────────────────────────────────────
@admin_bp.route("/dashboard_data")
def dashboard_admin_data():
    stats = [
        {"label": "Total Doctors",      "value": Doctor.query.count()},
        {"label": "Total Patients",     "value": Patient.query.count()},
        {"label": "Total Appointments", "value": Appointment.query.count()},
    ]

    upcoming = Appointment.query.filter_by(status="booked").limit(5).all()
    recent   = Appointment.query.order_by(Appointment.id.desc()).limit(5).all()

    return jsonify({
        "stats": stats,
        "upcoming": [
            {
                "id":      a.id,
                "patient": a.patient.name,
                "doctor":  a.doctor.name,
                "date":    str(a.date),
                "time":    str(a.time),
                "status":  a.status,
            } for a in upcoming
        ],
        "recent": [
            {
                "id":      a.id,
                "patient": a.patient.name,
                "doctor":  a.doctor.name,
                "date":    str(a.date),
                "status":  a.status,
            } for a in recent
        ],
    })


# ── ADD DOCTOR ─────────────────────────────────────────────────────────────────
@admin_bp.route("/add_doctor", methods=["POST"])
def add_doctor():
    data = request.json

    # basic validation
    if not data.get("name") or not data.get("specialization"):
        return jsonify({"msg": "Name and specialization are required"}), 400

    # create login account for doctor
    if User.query.filter_by(username=data["username"]).first():
        return jsonify({"msg": "Username already taken"}), 409

    user = User(
        username = data["username"],
        email    = data.get("email", f"{data['username']}@hospital.com"),
        role     = "doctor",
    )
    user.set_password(data.get("password", "Doctor@1234"))
    db.session.add(user)
    db.session.flush()   # get user.id before commit

    doctor = Doctor(
        user_id        = user.id,
        name           = data["name"],
        specialization = data["specialization"],
        phone          = data.get("phone", ""),
    )
    db.session.add(doctor)
    db.session.commit()

    return jsonify({"msg": "Doctor added successfully", "id": doctor.id}), 201


# ── UPDATE DOCTOR ──────────────────────────────────────────────────────────────
@admin_bp.route("/update_doctor/<int:doctor_id>", methods=["PUT"])
def update_doctor(doctor_id):
    doctor = Doctor.query.get_or_404(doctor_id)
    data   = request.json

    doctor.name           = data.get("name",           doctor.name)
    doctor.specialization = data.get("specialization", doctor.specialization)
    doctor.phone          = data.get("phone",          doctor.phone)
    doctor.availability   = data.get("availability",   doctor.availability)

    db.session.commit()
    return jsonify({"msg": "Doctor updated"})


# ── DELETE / BLACKLIST DOCTOR ──────────────────────────────────────────────────
@admin_bp.route("/delete_doctor/<int:doctor_id>", methods=["DELETE"])
def delete_doctor(doctor_id):
    doctor = Doctor.query.get_or_404(doctor_id)
    # deactivate user account instead of hard delete
    doctor.user.is_active = False
    db.session.commit()
    return jsonify({"msg": "Doctor deactivated"})


# ── DELETE APPOINTMENT ─────────────────────────────────────────────────────────
@admin_bp.route("/delete_appointment/<int:id>", methods=["DELETE"])
def delete_appointment(id):
    a = Appointment.query.get_or_404(id)
    db.session.delete(a)
    db.session.commit()
    return jsonify({"msg": "Appointment deleted"})


# ── SEARCH ─────────────────────────────────────────────────────────────────────
@admin_bp.route("/search")
def search():
    q = request.args.get("q", "").strip()

    if not q:
        return jsonify({"doctors": [], "patients": []})

    doctors = Doctor.query.filter(
        Doctor.name.ilike(f"%{q}%") | Doctor.specialization.ilike(f"%{q}%")
    ).all()

    patients = Patient.query.filter(
        Patient.name.ilike(f"%{q}%") | Patient.email.ilike(f"%{q}%")
    ).all()

    return jsonify({
        "doctors": [
            {"id": d.id, "name": d.name, "specialization": d.specialization, "phone": d.phone}
            for d in doctors
        ],
        "patients": [
            {"id": p.id, "name": p.name, "email": p.email, "phone": p.phone}
            for p in patients
        ],
    })


# ── LIST ALL DOCTORS (JSON for frontend) ──────────────────────────────────────
@admin_bp.route("/doctors")
def all_doctors():
    doctors = Doctor.query.all()
    return jsonify([
        {
            "id":             d.id,
            "name":           d.name,
            "specialization": d.specialization,
            "phone":          d.phone,
            "is_active":      d.user.is_active,
        }
        for d in doctors
    ])


# ── LIST ALL PATIENTS (JSON for frontend) ─────────────────────────────────────
@admin_bp.route("/patients")
def all_patients():
    patients = Patient.query.all()
    return jsonify([
        {
            "id":    p.id,
            "name":  p.name,
            "email": p.email,
            "phone": p.phone,
        }
        for p in patients
    ])


# ── ALL APPOINTMENTS ───────────────────────────────────────────────────────────
@admin_bp.route("/appointments")
def all_appointments():
    appointments = Appointment.query.order_by(Appointment.date.desc()).all()
    return jsonify([
        {
            "id":      a.id,
            "patient": a.patient.name,
            "doctor":  a.doctor.name,
            "date":    str(a.date),
            "time":    str(a.time),
            "status":  a.status,
        }
        for a in appointments
    ])


# ── BLACKLIST PATIENT ──────────────────────────────────────────────────────────
@admin_bp.route("/blacklist_patient/<int:patient_id>", methods=["POST"])
def blacklist_patient(patient_id):
    patient = Patient.query.get_or_404(patient_id)
    patient.user.is_active = False
    db.session.commit()
    return jsonify({"msg": "Patient deactivated"})