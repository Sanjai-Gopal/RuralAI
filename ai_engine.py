import re
from collections import defaultdict
from datetime import datetime

# ==============================
# Symptom Knowledge Base
# ==============================

SYMPTOM_WEIGHTS = {
    # High Risk
    "chest pain": 10,
    "breathlessness": 9,
    "unconscious": 12,
    "seizure": 10,
    "blood vomiting": 10,
    "stroke": 12,
    "paralysis": 11,
    "severe bleeding": 11,
    "heart attack": 12,

    # Moderate Risk
    "high fever": 6,
    "persistent cough": 5,
    "vomiting": 5,
    "diarrhea": 5,
    "abdominal pain": 5,
    "migraine": 5,
    "dizziness": 4,
    "dehydration": 5,
    "infection": 5,

    # Mild Risk
    "cold": 2,
    "fatigue": 3,
    "sore throat": 2,
    "body pain": 2,
    "mild fever": 3,
    "headache": 3,
    "cough": 2,
    "nausea": 2
}

# Severity Modifiers
SEVERITY_WORDS = {
    "severe": 3,
    "persistent": 2,
    "continuous": 2,
    "intense": 3,
    "extreme": 4
}

# Emergency Keywords
EMERGENCY_KEYWORDS = [
    "cannot breathe",
    "not breathing",
    "unconscious",
    "heavy bleeding",
    "collapse"
]

# ==============================
# AI ANALYSIS FUNCTION
# ==============================

def analyze_text(text, village="Unknown"):
    text = text.lower()
    detected_symptoms = []
    score = 0

    # Detect symptoms
    for symptom, weight in SYMPTOM_WEIGHTS.items():
        if symptom in text:
            detected_symptoms.append(symptom)
            score += weight

    # Detect severity modifiers
    severity_detected = []
    for word, weight in SEVERITY_WORDS.items():
        if word in text:
            severity_detected.append(word)
            score += weight

    # Detect emergency phrases
    emergency_flag = False
    for phrase in EMERGENCY_KEYWORDS:
        if phrase in text:
            emergency_flag = True
            score += 10

    # Detect duration
    duration_match = re.findall(r"(\d+\s*(day|days|week|weeks|month|months))", text)
    duration = duration_match[0][0] if duration_match else "not specified"

    # Risk Classification
    if score >= 20:
        risk_level = "HIGH RISK"
    elif score >= 10:
        risk_level = "MODERATE RISK"
    else:
        risk_level = "LOW RISK"

    explanation = {
        "detected_symptoms": detected_symptoms,
        "severity_words": severity_detected,
        "duration": duration,
        "emergency_flag": emergency_flag,
        "risk_reasoning": f"Risk score {score} calculated from weighted symptom and severity detection."
    }

    result = {
        "risk_level": risk_level,
        "risk_score": score,
        "explanation": explanation,
        "timestamp": datetime.now().isoformat(),
        "village": village
    }

    return result
