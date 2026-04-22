
# 🏥 CareConnect — Hospital Management System
 
![Python](https://img.shields.io/badge/Python-3.8+-blue?logo=python)
![Flask](https://img.shields.io/badge/Flask-3.0-black?logo=flask)
![Vue.js](https://img.shields.io/badge/Vue.js-2.0-green?logo=vue.js)
![SQLite](https://img.shields.io/badge/SQLite-database-lightblue?logo=sqlite)
![Redis](https://img.shields.io/badge/Redis-cache-red?logo=redis)
![Celery](https://img.shields.io/badge/Celery-5.4-green)
![Bootstrap](https://img.shields.io/badge/Bootstrap-5.3-purple?logo=bootstrap)
 

 
---
 
## 1. Project Description
 
CareConnect is a full-stack Hospital Management System (HMS) web application built for the Modern Application Development II course. It enables three types of users — Admins, Doctors, and Patients — to interact with the system based on their roles, replacing manual registers and disconnected software with a unified digital platform.
 
The system addresses key hospital challenges including scheduling conflicts, patient record tracking, and treatment history management. It provides real-time appointment booking, automated email notifications, and asynchronous report generation through background jobs.
 
### Core Objectives
- Provide role-based access control for Admin, Doctor, and Patient roles
- Enable patients to search doctors by specialization and book appointments
- Allow doctors to manage appointments and record treatment details
- Give admins complete oversight of the hospital system
- Automate daily reminders and monthly reports via Celery scheduled jobs
- Export patient treatment history as CSV on demand via async jobs
- Cache frequently accessed data using Redis to improve API performance
---
 
## 2. Technologies Used
 
| Category | Technology | Purpose |
|---|---|---|
| Backend Framework | Flask (Python) | REST API, routing, blueprints |
| Database | SQLite | Persistent relational data storage |
| ORM | Flask-SQLAlchemy | Database models and query abstraction |
| Authentication | Flask-JWT-Extended | JWT token-based role authentication |
| Frontend Framework | Vue.js 2 (CDN) | Reactive UI with custom delimiters |
| UI Styling | Bootstrap 5 | Responsive layout and components |
| Caching | Flask-Caching + Redis | API response caching with expiry |
| Task Queue | Celery + Redis | Async and scheduled background jobs |
| Email | Flask-Mail (SMTP) | Reminders, reports, CSV export alerts |
| DB Migrations | Flask-Migrate | Schema versioning without data loss |
| Password Security | Werkzeug | bcrypt password hashing |
 
---
 
## 3. System Architecture
 
CareConnect follows a client-server architecture with clear separation between frontend and backend layers. The backend exposes a RESTful API consumed by Vue.js templates rendered via Jinja2. Background tasks run asynchronously through Celery workers backed by Redis.
 
### 3.1 Architecture Layers
 
```
┌──────────────────────────────────────────────────────────┐
│                   PRESENTATION LAYER                      │
│   Vue.js 2 (CDN) + Bootstrap 5                           │
│   home.html | login.html | register.html                 │
│   dashboard_admin.html | dashboard_doctor.html           │
│   dashboard_patient.html                                 │
└────────────────────────┬─────────────────────────────────┘
                         │ HTTP / JSON (fetch API)
                         │ JWT Bearer Token
┌────────────────────────▼─────────────────────────────────┐
│                     API LAYER                             │
│   Flask Blueprints                                       │
│   auth_bp    → /register, /login                        │
│   admin_bp   → /admin/*                                 │
│   doctor_bp  → /doctor/*                                │
│   patient_bp → /patient/*                               │
└────────────────────────┬─────────────────────────────────┘
                         │
┌────────────────────────▼─────────────────────────────────┐
│                  BUSINESS LOGIC LAYER                     │
│   routes/auth.py   routes/admin.py                      │
│   routes/doctor.py routes/patient.py                    │
└────────────────────────┬─────────────────────────────────┘
                         │
┌────────────────────────▼─────────────────────────────────┐
│                    DATA LAYER                             │
│   SQLAlchemy ORM → SQLite (database.db)                 │
│   User | Doctor | Patient | Appointment                 │
│   Treatment | Department | DoctorAvailability           │
└──────────────────────────────────────────────────────────┘
                         │
┌────────────────────────▼─────────────────────────────────┐
│              CACHE + BACKGROUND JOBS LAYER                │
│   Redis ──► Flask-Caching (response cache)              │
│   Redis ──► Celery Broker                               │
│             ├── Daily Reminders (8 AM)                  │
│             ├── Monthly Reports (1st of month)          │
│             └── CSV Export (on demand)                  │
└──────────────────────────────────────────────────────────┘
```
 
### 3.2 Request Flow
 
1. User opens browser and loads HTML template served by Flask
2. Vue.js mounts on the page and calls Flask REST API via `fetch()`
3. JWT token is attached to every request via Authorization header
4. Flask validates token, executes route handler, queries SQLite via SQLAlchemy
5. Response is cached in Redis where applicable, returned as JSON
6. Vue.js updates the DOM reactively with response data
7. For background jobs, route calls `.delay()` which enqueues task in Redis
8. Celery worker picks up task, executes in Flask app context, sends email
### 3.3 Project Folder Structure
 
```
Application/
├── app.py                  ← Flask app factory, blueprints, DB seed
├── celery_app.py           ← Celery instance + task registration
├── celery_worker.py        ← make_celery() factory function
├── config.py               ← All configuration (DB, mail, Redis, JWT)
├── extensions.py           ← db, jwt, cache, mail instances
├── models.py               ← All SQLAlchemy models + seed functions
├── requirements.txt
├── routes/
│   ├── auth.py             ← /register, /login
│   ├── admin.py            ← /admin/* endpoints
│   ├── doctor.py           ← /doctor/* endpoints
│   └── patient.py          ← /patient/* endpoints
├── tasks/
│   ├── __init__.py
│   ├── reminders.py        ← Daily email reminder logic
│   ├── reports.py          ← Monthly HTML report logic
│   └── exports.py          ← CSV export logic
├── templates/
│   ├── home.html
│   ├── login.html
│   ├── register.html
│   ├── dashboard_admin.html
│   ├── dashboard_doctor.html
│   └── dashboard_patient.html
├── static/
│   └── js/
│       ├── login.js
│       ├── register.js
│       └── toast.js
├── instance/
│   └── database.db         ← SQLite database (auto-created)
└── exports/                ← Generated CSV files
```
 
---
 
## 4. Database Schema Design
 
All tables are created programmatically via `db.create_all()` on application startup. No manual database creation is used.
 
### 4.1 Entity Relationship Diagram
 
```
users (1) ──────────── (1) doctors
  │                          │
  │                          │ (1)
  └──── (1) patients         │
              │             availability
              │ (N)          │ (N)
              └──── appointments ────┘
                         │ (1)
                         │
                      treatments
                      
departments (1) ──── (N) doctors
```
 
### 4.2 Table Definitions
 
#### users
| Column | Type | Constraints | Description |
|---|---|---|---|
| id | Integer | PK | Auto-increment |
| username | String(50) | UNIQUE, NOT NULL | Login identifier |
| email | String(100) | UNIQUE, NOT NULL | Email for notifications |
| password | String(200) | NOT NULL | bcrypt hashed |
| role | String(20) | NOT NULL | admin / doctor / patient |
| is_active | Boolean | DEFAULT True | Blacklist flag |
 
#### departments
| Column | Type | Constraints | Description |
|---|---|---|---|
| id | Integer | PK | Auto-increment |
| name | String(100) | UNIQUE, NOT NULL | Department name |
| description | String(200) | NULLABLE | Brief description |
 
#### doctors
| Column | Type | Constraints | Description |
|---|---|---|---|
| id | Integer | PK | Auto-increment |
| user_id | Integer | FK users.id, NOT NULL | Login account link |
| department_id | Integer | FK departments.id | Department link |
| name | String(100) | NOT NULL | Full name |
| specialization | String(100) | NOT NULL | Medical specialty |
| phone | String(20) | NULLABLE | Contact number |
 
#### doctor_availability
| Column | Type | Constraints | Description |
|---|---|---|---|
| id | Integer | PK | Auto-increment |
| doctor_id | Integer | FK doctors.id, NOT NULL | Doctor link |
| avail_date | Date | NOT NULL | Available date |
| start_time | Time | NOT NULL | Slot start time |
| end_time | Time | NOT NULL | Slot end time |
| is_booked | Boolean | DEFAULT False | Slot taken flag |
| — | — | UNIQUE(doctor_id, avail_date, start_time) | No duplicate slots |
 
#### patients
| Column | Type | Constraints | Description |
|---|---|---|---|
| id | Integer | PK | Auto-increment |
| user_id | Integer | FK users.id, NOT NULL | Login account link |
| name | String(100) | NOT NULL | Full name |
| email | String(100) | NOT NULL | Contact email |
| phone | String(20) | NULLABLE | Contact number |
| address | String(200) | NULLABLE | Home address |
 
#### appointments
| Column | Type | Constraints | Description |
|---|---|---|---|
| id | Integer | PK | Auto-increment |
| patient_id | Integer | FK patients.id, NOT NULL | Booking patient |
| doctor_id | Integer | FK doctors.id, NOT NULL | Assigned doctor |
| date | Date | NOT NULL | Appointment date |
| time | Time | NOT NULL | Appointment time |
| status | String(20) | DEFAULT booked | booked / completed / cancelled |
| reason | String(200) | NULLABLE | Patient's stated reason |
| — | — | UNIQUE(doctor_id, date, time) | No double-booking |
 
#### treatments
| Column | Type | Constraints | Description |
|---|---|---|---|
| id | Integer | PK | Auto-increment |
| appointment_id | Integer | FK appointments.id, UNIQUE | One per appointment |
| diagnosis | String(200) | NOT NULL | Doctor's diagnosis |
| prescription | String(200) | NULLABLE | Prescribed medicines |
| notes | String(300) | NULLABLE | Additional doctor notes |
| next_visit | Date | NULLABLE | Suggested follow-up date |
 
### 4.3 Key Constraints
- **No double-booking**: `UniqueConstraint('doctor_id', 'date', 'time')` on appointments table enforced at DB level
- **No duplicate availability slots**: `UniqueConstraint('doctor_id', 'avail_date', 'start_time')` on doctor_availability
- **One treatment per appointment**: `unique=True` on `appointment_id` in treatments
- **Cascading relationships**: Deleting a doctor cascades to their appointments and availability slots
---
 
## 5. API Design
 
All endpoints follow RESTful conventions. Responses are JSON. Base URL: `http://localhost:5000`
 
### 5.1 OpenAPI Specification (YAML)
 
```yaml
openapi: 3.0.0
info:
  title: CareConnect HMS API
  description: Hospital Management System REST API
  version: 1.0.0
 
servers:
  - url: http://localhost:5000
 
components:
  securitySchemes:
    BearerAuth:
      type: http
      scheme: bearer
      bearerFormat: JWT
 
  schemas:
    LoginRequest:
      type: object
      required: [username, password]
      properties:
        username: { type: string }
        password: { type: string }
 
    RegisterRequest:
      type: object
      required: [username, email, password]
      properties:
        username: { type: string }
        email:    { type: string, format: email }
        password: { type: string, minLength: 6 }
        name:     { type: string }
        phone:    { type: string }
 
    TokenResponse:
      type: object
      properties:
        token:        { type: string }
        role:         { type: string, enum: [admin, doctor, patient] }
        patient_id:   { type: integer }
        patient_name: { type: string }
        doctor_id:    { type: integer }
        doctor_name:  { type: string }
 
    Doctor:
      type: object
      properties:
        id:             { type: integer }
        name:           { type: string }
        specialization: { type: string }
        phone:          { type: string }
        is_active:      { type: boolean }
 
    Patient:
      type: object
      properties:
        id:    { type: integer }
        name:  { type: string }
        email: { type: string }
        phone: { type: string }
 
    Appointment:
      type: object
      properties:
        id:      { type: integer }
        patient: { type: string }
        doctor:  { type: string }
        date:    { type: string, format: date }
        time:    { type: string }
        status:  { type: string, enum: [booked, completed, cancelled] }
        reason:  { type: string }
 
    Treatment:
      type: object
      properties:
        diagnosis:    { type: string }
        prescription: { type: string }
        notes:        { type: string }
        next_visit:   { type: string, format: date }
 
paths:
 
  # ── AUTH ──────────────────────────────────────────────────
  /register:
    post:
      tags: [Auth]
      summary: Register a new patient
      requestBody:
        required: true
        content:
          application/json:
            schema: { $ref: '#/components/schemas/RegisterRequest' }
      responses:
        '201':
          description: Registered successfully
          content:
            application/json:
              schema: { $ref: '#/components/schemas/TokenResponse' }
        '409': { description: Username or email already exists }
        '400': { description: Missing required fields }
 
  /login:
    post:
      tags: [Auth]
      summary: Login for all roles (Admin, Doctor, Patient)
      requestBody:
        required: true
        content:
          application/json:
            schema: { $ref: '#/components/schemas/LoginRequest' }
      responses:
        '200':
          description: Login successful
          content:
            application/json:
              schema: { $ref: '#/components/schemas/TokenResponse' }
        '401': { description: Invalid credentials }
        '403': { description: Account deactivated }
 
  # ── ADMIN ─────────────────────────────────────────────────
  /admin/dashboard_data:
    get:
      tags: [Admin]
      summary: Get admin dashboard stats and appointments
      responses:
        '200':
          description: Dashboard data
          content:
            application/json:
              schema:
                type: object
                properties:
                  stats:    { type: array, items: { type: object } }
                  upcoming: { type: array, items: { $ref: '#/components/schemas/Appointment' } }
                  recent:   { type: array, items: { $ref: '#/components/schemas/Appointment' } }
 
  /admin/add_doctor:
    post:
      tags: [Admin]
      summary: Add a new doctor with login credentials
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              required: [name, specialization, username]
              properties:
                name:           { type: string }
                specialization: { type: string }
                username:       { type: string }
                email:          { type: string }
                phone:          { type: string }
                password:       { type: string }
      responses:
        '201': { description: Doctor added successfully }
        '409': { description: Username already taken }
 
  /admin/update_doctor/{doctor_id}:
    put:
      tags: [Admin]
      summary: Update doctor profile
      parameters:
        - in: path
          name: doctor_id
          required: true
          schema: { type: integer }
      requestBody:
        content:
          application/json:
            schema:
              type: object
              properties:
                name:           { type: string }
                specialization: { type: string }
                phone:          { type: string }
      responses:
        '200': { description: Doctor updated }
        '404': { description: Doctor not found }
 
  /admin/delete_doctor/{doctor_id}:
    delete:
      tags: [Admin]
      summary: Deactivate a doctor account
      parameters:
        - in: path
          name: doctor_id
          required: true
          schema: { type: integer }
      responses:
        '200': { description: Doctor deactivated }
 
  /admin/delete_appointment/{id}:
    delete:
      tags: [Admin]
      summary: Delete an appointment
      parameters:
        - in: path
          name: id
          required: true
          schema: { type: integer }
      responses:
        '200': { description: Appointment deleted }
 
  /admin/search:
    get:
      tags: [Admin]
      summary: Search doctors and patients
      parameters:
        - in: query
          name: q
          required: true
          schema: { type: string }
      responses:
        '200':
          description: Search results
          content:
            application/json:
              schema:
                type: object
                properties:
                  doctors:  { type: array, items: { $ref: '#/components/schemas/Doctor' } }
                  patients: { type: array, items: { $ref: '#/components/schemas/Patient' } }
 
  /admin/doctors:
    get:
      tags: [Admin]
      summary: List all doctors (cached 2 min)
      responses:
        '200':
          content:
            application/json:
              schema:
                type: array
                items: { $ref: '#/components/schemas/Doctor' }
 
  /admin/patients:
    get:
      tags: [Admin]
      summary: List all patients (cached 2 min)
      responses:
        '200':
          content:
            application/json:
              schema:
                type: array
                items: { $ref: '#/components/schemas/Patient' }
 
  /admin/appointments:
    get:
      tags: [Admin]
      summary: List all appointments
      responses:
        '200':
          content:
            application/json:
              schema:
                type: array
                items: { $ref: '#/components/schemas/Appointment' }
 
  /admin/blacklist_patient/{patient_id}:
    post:
      tags: [Admin]
      summary: Deactivate a patient account
      parameters:
        - in: path
          name: patient_id
          required: true
          schema: { type: integer }
      responses:
        '200': { description: Patient deactivated }
 
  # ── DOCTOR ────────────────────────────────────────────────
  /doctor/dashboard_data/{doc_id}:
    get:
      tags: [Doctor]
      summary: Get doctor dashboard data
      parameters:
        - in: path
          name: doc_id
          required: true
          schema: { type: integer }
      responses:
        '200':
          content:
            application/json:
              schema:
                type: object
                properties:
                  stats:       { type: array }
                  today:       { type: array }
                  week:        { type: array }
                  patients:    { type: array }
                  doctor_name: { type: string }
 
  /doctor/appointments/{doc_id}:
    get:
      tags: [Doctor]
      summary: Get all appointments for a doctor
      parameters:
        - in: path
          name: doc_id
          required: true
          schema: { type: integer }
      responses:
        '200':
          content:
            application/json:
              schema:
                type: array
                items: { $ref: '#/components/schemas/Appointment' }
 
  /doctor/complete/{appointment_id}:
    post:
      tags: [Doctor]
      summary: Mark appointment complete and save treatment
      parameters:
        - in: path
          name: appointment_id
          required: true
          schema: { type: integer }
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              required: [diagnosis]
              properties:
                diagnosis:    { type: string }
                prescription: { type: string }
                notes:        { type: string }
      responses:
        '200': { description: Appointment completed and treatment saved }
        '404': { description: Appointment not found }
        '400': { description: Diagnosis required }
 
  /doctor/cancel/{appointment_id}:
    post:
      tags: [Doctor]
      summary: Cancel an appointment
      parameters:
        - in: path
          name: appointment_id
          required: true
          schema: { type: integer }
      responses:
        '200': { description: Appointment cancelled }
 
  /doctor/patient_history/{patient_id}:
    get:
      tags: [Doctor]
      summary: Get full treatment history of a patient
      parameters:
        - in: path
          name: patient_id
          required: true
          schema: { type: integer }
      responses:
        '200':
          content:
            application/json:
              schema:
                type: array
                items: { $ref: '#/components/schemas/Treatment' }
 
  /doctor/availability:
    post:
      tags: [Doctor]
      summary: Set availability slots for next 7 days
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              required: [doctor_id, slots]
              properties:
                doctor_id: { type: integer }
                slots:
                  type: array
                  items:
                    type: object
                    properties:
                      date:  { type: string, format: date }
                      start: { type: string, example: "09:00" }
                      end:   { type: string, example: "17:00" }
      responses:
        '200': { description: Slots saved }
 
  /doctor/availability/{doc_id}:
    get:
      tags: [Doctor]
      summary: Get availability slots for a doctor (cached 5 min)
      parameters:
        - in: path
          name: doc_id
          required: true
          schema: { type: integer }
      responses:
        '200':
          content:
            application/json:
              schema:
                type: array
                items:
                  type: object
                  properties:
                    id:        { type: integer }
                    date:      { type: string }
                    start:     { type: string }
                    end:       { type: string }
                    is_booked: { type: boolean }
 
  # ── PATIENT ───────────────────────────────────────────────
  /patient/dashboard_data/{patient_id}:
    get:
      tags: [Patient]
      summary: Get patient dashboard data
      parameters:
        - in: path
          name: patient_id
          required: true
          schema: { type: integer }
      responses:
        '200':
          content:
            application/json:
              schema:
                type: object
                properties:
                  stats:    { type: array }
                  upcoming: { type: array }
                  past:     { type: array }
                  patient:  { type: object }
 
  /patient/departments:
    get:
      tags: [Patient]
      summary: List all departments with doctor count (cached 10 min)
      responses:
        '200':
          content:
            application/json:
              schema:
                type: array
                items:
                  type: object
                  properties:
                    id:           { type: integer }
                    name:         { type: string }
                    description:  { type: string }
                    doctor_count: { type: integer }
 
  /patient/doctors:
    get:
      tags: [Patient]
      summary: List doctors with 7-day availability
      parameters:
        - in: query
          name: specialization
          schema: { type: string }
          description: Filter by specialization or department name
      responses:
        '200':
          content:
            application/json:
              schema:
                type: array
                items: { $ref: '#/components/schemas/Doctor' }
 
  /patient/book:
    post:
      tags: [Patient]
      summary: Book an appointment
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              required: [patient_id, doctor_id, date, time]
              properties:
                patient_id: { type: integer }
                doctor_id:  { type: integer }
                date:       { type: string, format: date }
                time:       { type: string, example: "09:00" }
                reason:     { type: string }
                slot_id:    { type: integer }
      responses:
        '201': { description: Appointment booked successfully }
        '409': { description: Slot already booked }
        '400': { description: Missing required fields }
 
  /patient/cancel/{appointment_id}:
    post:
      tags: [Patient]
      summary: Cancel an appointment
      parameters:
        - in: path
          name: appointment_id
          required: true
          schema: { type: integer }
      responses:
        '200': { description: Appointment cancelled }
        '400': { description: Only booked appointments can be cancelled }
 
  /patient/profile/{patient_id}:
    put:
      tags: [Patient]
      summary: Update patient profile
      parameters:
        - in: path
          name: patient_id
          required: true
          schema: { type: integer }
      requestBody:
        content:
          application/json:
            schema:
              type: object
              properties:
                name:    { type: string }
                email:   { type: string }
                phone:   { type: string }
                address: { type: string }
      responses:
        '200': { description: Profile updated }
        '409': { description: Email already in use }
 
  /patient/history/{patient_id}:
    get:
      tags: [Patient]
      summary: Get full treatment history for a patient
      parameters:
        - in: path
          name: patient_id
          required: true
          schema: { type: integer }
      responses:
        '200':
          content:
            application/json:
              schema:
                type: array
                items: { $ref: '#/components/schemas/Treatment' }
 
  /patient/search:
    get:
      tags: [Patient]
      summary: Search doctors by name or specialization
      parameters:
        - in: query
          name: q
          required: true
          schema: { type: string }
      responses:
        '200':
          content:
            application/json:
              schema:
                type: array
                items: { $ref: '#/components/schemas/Doctor' }
 
  /patient/export_csv/{patient_id}:
    post:
      tags: [Patient]
      summary: Trigger async CSV export of treatment history
      parameters:
        - in: path
          name: patient_id
          required: true
          schema: { type: integer }
      responses:
        '202':
          description: Export started, email sent on completion
          content:
            application/json:
              schema:
                type: object
                properties:
                  msg:     { type: string }
                  task_id: { type: string }
```
 
---
 
## 6. Features
 
### 6.1 Admin Features
- Pre-seeded admin account created programmatically on startup (no registration)
- Dashboard with total counts of doctors, patients, and appointments
- Add new doctors with login credentials (username, email, password)
- Update doctor profiles (name, specialization, phone)
- Deactivate/blacklist doctors and patients
- View all appointments with status badges
- Delete appointments
- Search doctors by name or specialization
- Search patients by name or email
- View all doctors and patients in tabular format
### 6.2 Doctor Features
- Login-only access (added by admin, no self-registration)
- Dashboard with today's and this week's upcoming appointments
- Tab-based view: Today / This Week / All Appointments / My Patients
- Mark appointments as completed with diagnosis, prescription, and notes
- Cancel appointments
- View full treatment history of any assigned patient
- Set availability slots for the next 7 days (date + start/end time)
- View current availability with booked/free status indicators
### 6.3 Patient Features
- Self-registration and login
- Dashboard with upcoming appointments and past history
- Browse all departments with active doctor counts
- Find doctors filtered by specialization or department
- View doctor availability slots for next 7 days
- Book appointments by selecting a doctor and slot
- Cancel booked appointments
- View past appointment history with diagnosis, prescription, notes, and next visit date
- Edit personal profile (name, email, phone, address)
- Export full treatment history as CSV via async background job
### 6.4 Backend Jobs
 
#### Job a — Daily Appointment Reminders
- Scheduled via Celery beat at 8:00 AM every day (Asia/Kolkata timezone)
- Queries all appointments with status `booked` for today's date
- Sends a styled HTML email to each patient with doctor name, date, and time
- Advises patients to arrive 10 minutes early
#### Job b — Monthly Doctor Activity Report
- Scheduled on the 1st of every month at 7:00 AM
- For each doctor, queries all appointments from the previous month
- Builds a full HTML report with summary stats (total, completed, cancelled, booked)
- Includes a detailed table of all appointments with diagnosis and prescription
- Sent via email to each doctor's registered email address
#### Job c — Patient CSV Export (Async, User-Triggered)
- Triggered by patient clicking "Export Treatment History" on their dashboard
- Celery task executes asynchronously via `.delay()`
- Generates a CSV file with: User ID, Username, Patient Name, Consulting Doctor, Specialization, Date, Time, Status, Diagnosis, Prescription, Notes, Next Visit
- CSV saved to `exports/` folder and sent as email attachment
- Patient sees a toast notification: "Export started. You will receive an email when it's ready."
### 6.5 Caching
 
| Route | Cache Key | Timeout | Busted When |
|---|---|---|---|
| GET /admin/dashboard_data | admin_dashboard | 60 seconds | Doctor added |
| GET /admin/doctors | admin_all_doctors | 120 seconds | Doctor added/deactivated |
| GET /admin/patients | admin_all_patients | 120 seconds | — |
| GET /patient/departments | departments | 600 seconds | — |
| GET /doctor/availability/<id> | avail_<doc_id> | 300 seconds | Slots added |
 
### 6.6 Security Features
- Passwords hashed using bcrypt via Werkzeug
- JWT tokens with role embedded in payload
- `is_active` flag for blacklisting users without deletion
- Double-booking prevention via DB-level UniqueConstraint
- Generic error messages on login to prevent username enumeration
### 6.7 UI Features
- Consistent dark blue gradient theme (`#0f2027 → #2c5364`) across all pages
- Toast notification system replacing browser `alert()` dialogs
- Colour-coded appointment status badges (yellow=booked, green=completed, red=cancelled)
- Tab-based navigation on doctor and patient dashboards
- Modal overlays for forms (add doctor, complete appointment, book appointment, edit profile)
- Responsive layout using Bootstrap 5 grid
---
 
## 7. How to Run
 
### Prerequisites
- Python 3.8+
- Redis server
- Node.js (optional, only for report generation)
### Installation
```bash
pip install -r requirements.txt
```
 
### Running the Application
 
Open 4 terminals in the project root:
 
```bash
# Terminal 1 — Redis
redis-server
 
# Terminal 2 — Flask
python app.py
 
# Terminal 3 — Celery Worker
celery -A celery_app.celery worker --pool=solo --loglevel=info
 
# Terminal 4 — Celery Beat (scheduler)
celery -A celery_app.celery beat --loglevel=info
```
 
### Default Credentials
| Role | Username | Password |
|---|---|---|
| Admin | admin | Admin@1234 |
| Doctor | (set when added by admin) | Doctor@1234 (default) |
| Patient | (self-registered) | (chosen at registration) |
 
---
 
*CareConnect Hospital Management System — MAD II Project — 2025–2026*
