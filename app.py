from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os
import re
from collections import defaultdict
import json

# =========================================
# APP CONFIGURATION
# =========================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app = Flask(
    __name__,
    static_folder=os.path.join(BASE_DIR, "static"),
    template_folder=os.path.join(BASE_DIR, "templates")
)

app.config["SECRET_KEY"] = "ultra_secure_secret_key"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.login_view = "login"
login_manager.init_app(app)

# =========================================
# DATABASE MODELS
# =========================================

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(150))
    email = db.Column(db.String(150), unique=True)
    password = db.Column(db.String(200))
    role = db.Column(db.String(50))
    village = db.Column(db.String(150))
    age = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Case(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    symptoms = db.Column(db.Text)
    village = db.Column(db.String(150))
    risk_level = db.Column(db.String(50))
    risk_score = db.Column(db.Integer)
    explanation = db.Column(db.Text)
    doctor_override = db.Column(db.String(50), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

with app.app_context():
    db.create_all()

# =========================================
# TEST ROUTE
# =========================================

@app.route("/test")
def test():
    return "Server Updated Successfully ✅"

# =========================================
# SIMPLE NLP ENGINE (No spaCy)
# =========================================

SYMPTOM_WEIGHTS = {
    "chest pain": 10,
    "breathlessness": 9,
    "shortness of breath": 9,
    "unconscious": 12,
    "seizure": 10,
    "vomiting blood": 11,
    "stroke": 12,
    "high fever": 7,
    "persistent cough": 6,
    "diarrhea": 5,
    "abdominal pain": 6,
    "headache": 4,
    "migraine": 5,
    "fatigue": 3,
    "dizziness": 4,
    "infection": 5,
    "cold": 2,
    "sore throat": 3,
    "body pain": 3,
    "nausea": 3
}

SEVERITY_MODIFIERS = {
    "severe": 3,
    "extreme": 4,
    "persistent": 2,
    "continuous": 2,
    "intense": 3
}

EMERGENCY_PATTERNS = [
    "cannot breathe",
    "not breathing",
    "collapsed",
    "losing consciousness",
    "heavy bleeding"
]

def analyze_text(text, village="Unknown"):
    text_lower = text.lower()

    detected_symptoms = []
    detected_severity = []
    score = 0
    emergency_flag = False

    # Symptom detection
    for symptom, weight in SYMPTOM_WEIGHTS.items():
        if symptom in text_lower:
            detected_symptoms.append(symptom)
            score += weight

    # Severity detection
    for word, value in SEVERITY_MODIFIERS.items():
        if word in text_lower:
            detected_severity.append(word)
            score += value

    # Emergency detection
    for pattern in EMERGENCY_PATTERNS:
        if pattern in text_lower:
            emergency_flag = True
            score += 15

    # Duration detection
    duration_match = re.findall(r"(\d+\s*(day|days|week|weeks|month|months|hour|hours))", text_lower)
    duration = duration_match[0][0] if duration_match else "not specified"

    # Risk classification
    if emergency_flag or score >= 20:
        risk = "HIGH RISK"
    elif score >= 10:
        risk = "MODERATE RISK"
    else:
        risk = "LOW RISK"

    reasoning = {
        "detected_symptoms": detected_symptoms,
        "severity_modifiers": detected_severity,
        "emergency_detected": emergency_flag,
        "duration": duration,
        "final_score": score,
        "explanation": "Risk calculated using keyword-based weighted scoring."
    }

    return risk, score, reasoning

# =========================================
# AUTH ROUTES
# =========================================

@app.route("/")
def home():
    if current_user.is_authenticated:
        if current_user.role == "doctor":
            return redirect(url_for("doctor_dashboard"))
        return redirect(url_for("patient_dashboard"))
    return redirect(url_for("login"))

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password, password):
            login_user(user)
            if user.role == "doctor":
                return redirect(url_for("doctor_dashboard"))
            return redirect(url_for("patient_dashboard"))

        flash("Invalid credentials")

    return render_template("login.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        full_name = request.form.get("full_name")
        email = request.form.get("email")
        password = request.form.get("password")
        role = request.form.get("role")
        village = request.form.get("village")
        age = request.form.get("age")

        if User.query.filter_by(email=email).first():
            flash("Email already exists")
            return redirect(url_for("register"))

        hashed = generate_password_hash(password)

        new_user = User(
            full_name=full_name,
            email=email,
            password=hashed,
            role=role,
            village=village,
            age=int(age)
        )

        db.session.add(new_user)
        db.session.commit()

        flash("Account created successfully")
        return redirect(url_for("login"))

    return render_template("register.html")

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))

# =========================================
# PATIENT DASHBOARD
# =========================================

@app.route("/patient")
@login_required
def patient_dashboard():
    if current_user.role != "patient":
        return redirect(url_for("login"))
    cases = Case.query.filter_by(patient_id=current_user.id).all()
    return render_template("patient_dashboard.html", cases=cases)

@app.route("/analyze", methods=["POST"])
@login_required
def analyze():
    if current_user.role != "patient":
        return jsonify({"error": "Unauthorized"}), 403

    data = request.json
    text = data.get("text", "")

    if not text:
        return jsonify({"error": "No symptoms provided"}), 400

    risk, score, explanation = analyze_text(text, current_user.village)

    new_case = Case(
        patient_id=current_user.id,
        symptoms=text,
        village=current_user.village,
        risk_level=risk,
        risk_score=score,
        explanation=json.dumps(explanation)
    )

    db.session.add(new_case)
    db.session.commit()

    if risk == "HIGH RISK":
        suggestion_text = "Please visit the nearest hospital immediately."
    elif risk == "MODERATE RISK":
        suggestion_text = "Consult a doctor within 24-48 hours."
    else:
        suggestion_text = "Rest and monitor symptoms."

    return jsonify({
        "risk_level": risk,
        "suggestion": suggestion_text
    })

# =========================================
# DOCTOR DASHBOARD
# =========================================

@app.route("/doctor")
@login_required
def doctor_dashboard():
    if current_user.role != "doctor":
        return redirect(url_for("login"))
    cases = Case.query.all()
    return render_template("doctor_dashboard.html", cases=cases)

@app.route("/doctor/override", methods=["POST"])
@login_required
def doctor_override():
    if current_user.role != "doctor":
        return jsonify({"error": "Unauthorized"}), 403

    case_id = request.json.get("case_id")
    override = request.json.get("override")

    case = Case.query.get(case_id)
    if case:
        case.doctor_override = override
        db.session.commit()
        return jsonify({"status": "Override saved"})

    return jsonify({"error": "Case not found"}), 404

# =========================================
# ANALYTICS
# =========================================

@app.route("/analytics")
@login_required
def analytics():
    if current_user.role != "doctor":
        return jsonify({"error": "Unauthorized"}), 403

    risk_distribution = defaultdict(int)
    village_distribution = defaultdict(int)

    cases = Case.query.all()

    for case in cases:
        risk_distribution[case.risk_level] += 1
        village_distribution[case.village] += 1

    return jsonify({
        "risk_distribution": dict(risk_distribution),
        "village_distribution": dict(village_distribution),
        "total_cases": len(cases)
    })

# =========================================
# RUN
# =========================================

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
