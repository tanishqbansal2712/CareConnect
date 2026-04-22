from flask import Flask, render_template, jsonify, request
from extensions import db, jwt, cache, mail
from config import Config
from flask_cors import CORS

from routes.auth    import auth_bp
from routes.admin   import admin_bp
from routes.doctor  import doctor_bp
from routes.patient import patient_bp

app = Flask(__name__)
app.config.from_object(Config)

CORS(app)

db.init_app(app)
jwt.init_app(app)
cache.init_app(app)
mail.init_app(app)

# register blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(doctor_bp)
app.register_blueprint(patient_bp)

with app.app_context():
    db.create_all()

    # seed admin —
    from models import User, Department
    if not User.query.filter_by(role="admin").first():
        from models import User
        admin = User(username="admin", email="admin@hospital.com", role="admin")
        admin.set_password("Admin@1234")
        db.session.add(admin)
        db.session.commit()
        print("Admin seeded.")

    # seed departments
    if Department.query.count() == 0:
        depts = [
            ("Cardiology",       "Heart and blood vessels"),
            ("Neurology",        "Brain and nervous system"),
            ("Orthopedics",      "Bones and joints"),
            ("Pediatrics",       "Children health"),
            ("General Medicine", "Primary care"),
            ("Dermatology",      "Skin conditions"),
            ("ENT",              "Ear, Nose, Throat"),
            ("Gynecology",       "Female health"),
        ]
        for name, desc in depts:
            db.session.add(Department(name=name, description=desc))
        db.session.commit()
        print("Departments seeded.")



# ── CSV Export trigger (Job c) ─────────────────────────────────────────────────
@app.route("/patient/export_csv/<int:patient_id>", methods=["POST"])
def trigger_export(patient_id):
    try:
        from celery_app import export_patient_csv, celery
        job = export_patient_csv.delay(patient_id)
        return jsonify({
            "msg":     "Export started. You will receive an email when it\'s ready.",
            "task_id": job.id
        }), 202
    except Exception as e:
        return jsonify({"msg": f"Could not start export: {str(e)}"}), 500


# ── HTML page routes ───────────────────────────────────────────────────────────
@app.route("/")
def home():
    return render_template("home.html")

@app.route("/login/<role>")
def login_page(role):
    return render_template("login.html")

@app.route("/register/patient")
def register_page():
    return render_template("register.html")

@app.route("/dashboard_admin")
def admin_dashboard():
    return render_template("dashboard_admin.html")

@app.route("/dashboard_doctor")
def doctor_dashboard():
    return render_template("dashboard_doctor.html")

@app.route("/dashboard_patient")
def patient_dashboard():
    return render_template("dashboard_patient.html")


if __name__ == "__main__":
    app.run(debug=True)