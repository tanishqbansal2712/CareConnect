from flask import Blueprint, request, jsonify
from models import User, Patient
from extensions import db
from flask_jwt_extended import create_access_token

auth_bp = Blueprint("auth", __name__)


# REGISTER — patients only
@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.json

    # basic validation
    if not data.get("username") or not data.get("password") or not data.get("email"):
        return jsonify({"msg": "username, email and password are required"}), 400

    if User.query.filter_by(username=data["username"]).first():
        return jsonify({"msg": "Username already taken"}), 409

    if User.query.filter_by(email=data["email"]).first():
        return jsonify({"msg": "Email already registered"}), 409

    # create User
    user = User(
        username = data["username"],
        email    = data["email"],
        role     = "patient"
    )
    user.set_password(data["password"])   
    db.session.add(user)
    db.session.flush()   # get user.id before commit

    # create linked Patient profile
    patient = Patient(
        user_id = user.id,            
        name    = data.get("name", data["username"]),
        email   = data["email"],
        phone   = data.get("phone", "")
    )
    db.session.add(patient)
    db.session.commit()

    token = create_access_token(identity={"id": user.id, "role": user.role})
    return jsonify({"msg": "Registered successfully", "token": token, "role": user.role}), 201


# LOGIN — all roles
@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.json

    if not data.get("username") or not data.get("password"):
        return jsonify({"msg": "username and password are required"}), 400

    user = User.query.filter_by(username=data["username"]).first()

    if not user or not user.check_password(data["password"]):
        return jsonify({"msg": "Invalid username or password"}), 401

    if not user.is_active:
        return jsonify({"msg": "Your account has been deactivated"}), 403

    token = create_access_token(identity={"id": user.id, "role": user.role})

    # include profile id so the frontend can store it in localStorage
    extra = {}
    if user.role == "patient" and user.patient_profile:
        extra["patient_id"]   = user.patient_profile.id
        extra["patient_name"] = user.patient_profile.name
    elif user.role == "doctor" and user.doctor_profile:
        extra["doctor_id"]   = user.doctor_profile.id
        extra["doctor_name"] = user.doctor_profile.name

    return jsonify({
        "token": token,
        "role":  user.role,
        "msg":   f"Welcome {user.username}",
        **extra
    }), 200