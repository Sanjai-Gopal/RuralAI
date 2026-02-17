from flask import Flask, render_template, request, jsonify
import os
import re
from collections import defaultdict
from datetime import datetime

app = Flask(__name__)

# ==============================
# In-Memory Storage (Hackathon Safe)
# ==============================

cases_db = []
doctor_feedback_db = []

# ==============================
# Advanced Symptom Intelligence
# ==============================

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

# ==============================
# AI ANALYSIS ENGINE
# ==============================

def analyze_text(text, village="Unknown"):
    text = text.lower()
    score = 0
    detected = []

    # Symptom scoring
    for symptom, weight in HIGH_RISK.items():
        if symptom in text:
            score += weight
            detected.append(symptom)

    for symptom, weight in MODERATE_RISK.items():
        if symptom in text:
            score += weight
            detected.append(symptom)

    for symptom, weight in MILD_RISK.items():
        if symptom in text:
            score += weight
            detected.append(symptom)

    # Severity detection
    severity = "normal"
    if "severe" in text or "persistent" in text:
        severity = "high"
        score += 2

    # Duration detection
    duration_match = re.findall(r"(\d+\s*(day|days|week|weeks|month|months))", text)
    duration = duration_match[0][0] if duration_match else "not specified"

    # Risk classification
    if score >= 12:
        risk = "HIGH RISK"
    elif score >= 6:
        risk = "MODERATE RISK"
    else:
        risk = "LOW RISK"

    explanation = {
        "detected_symptoms": detected,
        "severity": severity,
        "duration": duration,
        "risk_reasoning": f"Total score {score} based on weighted symptom detection."
    }

    result = {
        "risk_level": risk,
        "risk_score": score,
        "explanation": explanation,
        "timestamp": datetime.now().isoformat(),
        "village": village
    }

    cases_db.append(result)
    return result

# ==============================
# ROUTES
# ==============================

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/analyze", methods=["POST"])
def analyze():
    data = request.json
    text = data.get("text", "")
    village = data.get("village", "Unknown")

    if not text:
        return jsonify({"error": "No symptoms provided"}), 400

    result = analyze_text(text, village)
    return jsonify(result)

@app.route("/doctor/feedback", methods=["POST"])
def doctor_feedback():
    data = request.json
    case_id = data.get("case_index")
    override_risk = data.get("override_risk")

    if case_id is None or override_risk is None:
        return jsonify({"error": "Invalid feedback data"}), 400

    if 0 <= case_id < len(cases_db):
        cases_db[case_id]["doctor_override"] = override_risk
        doctor_feedback_db.append({
            "case_index": case_id,
            "override": override_risk,
            "timestamp": datetime.now().isoformat()
        })
        return jsonify({"status": "Feedback recorded"})
    else:
        return jsonify({"error": "Invalid case index"}), 400

@app.route("/analytics")
def analytics():
    risk_distribution = defaultdict(int)
    village_distribution = defaultdict(int)

    for case in cases_db:
        risk_distribution[case["risk_level"]] += 1
        village_distribution[case["village"]] += 1

    return jsonify({
        "risk_distribution": risk_distribution,
        "village_distribution": village_distribution,
        "total_cases": len(cases_db)
    })

# ==============================
# Render Production Config
# ==============================

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
