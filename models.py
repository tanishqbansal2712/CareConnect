from extensions import db
from datetime import datetime, date
from werkzeug.security import generate_password_hash, check_password_hash


class User(db.Model):
    __tablename__ = 'users'

    id        = db.Column(db.Integer, primary_key=True)
    username  = db.Column(db.String(50),  unique=True, nullable=False)
    email     = db.Column(db.String(100), unique=True, nullable=False)
    password  = db.Column(db.String(200), nullable=False)
    role      = db.Column(db.String(20),  nullable=False)   # admin | doctor | patient
    is_active = db.Column(db.Boolean, default=True)

    def set_password(self, raw):
        self.password = generate_password_hash(raw)

    def check_password(self, raw):
        return check_password_hash(self.password, raw)


class Department(db.Model):
    __tablename__ = 'departments'

    id          = db.Column(db.Integer, primary_key=True)
    name        = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.String(200))

    doctors = db.relationship('Doctor', backref='department', lazy=True)


class Doctor(db.Model):
    __tablename__ = 'doctors'

    id             = db.Column(db.Integer, primary_key=True)
    user_id        = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    department_id  = db.Column(db.Integer, db.ForeignKey('departments.id'))
    name           = db.Column(db.String(100), nullable=False)
    specialization = db.Column(db.String(100), nullable=False)
    phone          = db.Column(db.String(20))

    user         = db.relationship('User', backref=db.backref('doctor_profile', uselist=False))
    appointments = db.relationship('Appointment', backref='doctor', lazy=True)
    slots        = db.relationship('DoctorAvailability', backref='doctor', lazy=True)


class DoctorAvailability(db.Model):
    __tablename__ = 'doctor_availability'

    id         = db.Column(db.Integer, primary_key=True)
    doctor_id  = db.Column(db.Integer, db.ForeignKey('doctors.id'), nullable=False)
    avail_date = db.Column(db.Date,    nullable=False)
    start_time = db.Column(db.Time,    nullable=False)
    end_time   = db.Column(db.Time,    nullable=False)
    is_booked  = db.Column(db.Boolean, default=False)

    __table_args__ = (
        db.UniqueConstraint('doctor_id', 'avail_date', 'start_time', name='uq_doctor_avail_slot'),
    )


class Patient(db.Model):
    __tablename__ = 'patients'

    id      = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name    = db.Column(db.String(100), nullable=False)
    email   = db.Column(db.String(100), nullable=False)
    phone   = db.Column(db.String(20))
    address = db.Column(db.String(200))

    user         = db.relationship('User', backref=db.backref('patient_profile', uselist=False))
    appointments = db.relationship('Appointment', backref='patient', lazy=True)


class Appointment(db.Model):
    __tablename__ = 'appointments'

    id         = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)
    doctor_id  = db.Column(db.Integer, db.ForeignKey('doctors.id'),  nullable=False)
    date       = db.Column(db.Date, nullable=False)
    time       = db.Column(db.Time, nullable=False)
    status     = db.Column(db.String(20), default='booked')  # booked | completed | cancelled
    reason     = db.Column(db.String(200))

    # no double-booking: same doctor can't have two appointments at same date+time
    __table_args__ = (
        db.UniqueConstraint('doctor_id', 'date', 'time', name='uq_doctor_slot'),
    )

    treatment = db.relationship('Treatment', backref='appointment', uselist=False)


class Treatment(db.Model):
    __tablename__ = 'treatments'

    id             = db.Column(db.Integer, primary_key=True)
    appointment_id = db.Column(db.Integer, db.ForeignKey('appointments.id'), nullable=False, unique=True)
    diagnosis      = db.Column(db.String(200), nullable=False)
    prescription   = db.Column(db.String(200))
    notes          = db.Column(db.String(300))
    next_visit     = db.Column(db.Date)


# ── seed functions ─────────────────────────────────────────────────────────────

def seed_admin():
    if not User.query.filter_by(role='admin').first():
        admin = User(username='admin', email='admin@hospital.com', role='admin')
        admin.set_password('Admin@1234')
        db.session.add(admin)
        db.session.commit()
        print('Admin created.')


def seed_departments():
    if Department.query.count() == 0:
        depts = [
            ('Cardiology',       'Heart and blood vessels'),
            ('Neurology',        'Brain and nervous system'),
            ('Orthopedics',      'Bones and joints'),
            ('Pediatrics',       'Children health'),
            ('General Medicine', 'Primary care'),
            ('Dermatology',      'Skin conditions'),
            ('ENT',              'Ear, Nose, Throat'),
            ('Gynecology',       'Female health'),
        ]
        for name, desc in depts:
            db.session.add(Department(name=name, description=desc))
        db.session.commit()
        print(f'{len(depts)} departments added.')