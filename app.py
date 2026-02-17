from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os
import re
from collections import defaultdict

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
    role = db.Column(db.String(50))  # patient or doctor
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
# ADVANCED AI ENGINE (KEPT FROM BEFORE)
# =========================================

HIGH_RISK = {
    "chest pain": 8,
    "breathlessness": 8,
    "unconscious": 10,
    "seizure": 9,
    "blood vomiting": 9,
    "stroke": 10,
}

MODERATE_RISK = {
    "high fever": 5,
    "persistent cough": 5,
    "vomiting": 4,
    "diarrhea": 4,
    "severe headache": 5,
    "abdominal pain": 5,
}

MILD_RISK = {
    "cold": 1,
    "fatigue": 2,
    "sore throat": 2,
    "body pain": 2,
    "mild fever": 2,
}

def analyze_text(text, village="Unknown"):
    text = text.lower()
    score = 0
    detected = []

    for group in [HIGH_RISK, MODERATE_RISK, MILD_RISK]:
        for symptom, weight in group.items():
            if symptom in text:
                score += weight
                detected.append(symptom)

    if "severe" in text or "persistent" in text:
        score += 2

    duration_match = re.findall(r"(\d+\s*(day|days|week|weeks|month|months))", text)
    duration = duration_match[0][0] if duration_match else "not specified"

    if score >= 12:
        risk = "HIGH RISK"
    elif score >= 6:
        risk = "MODERATE RISK"
    else:
        risk = "LOW RISK"

    explanation = f"Detected: {', '.join(detected)} | Duration: {duration}"

    return risk, score, explanation

# =========================================
# AUTHENTICATION ROUTES
# =========================================

@app.route("/")
def home():
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

@app.route("/forgot")
def forgot():
    return render_template("forgot.html")

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
        explanation=explanation
    )

    db.session.add(new_case)
    db.session.commit()

    # Patient DOES NOT see score
    return jsonify({
        "risk_level": risk,
        "suggestion": explanation
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
# ANALYTICS (DOCTOR ONLY)
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
        "risk_distribution": risk_distribution,
        "village_distribution": village_distribution,
        "total_cases": len(cases)
    })

# =========================================
# RUN
# =========================================

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
