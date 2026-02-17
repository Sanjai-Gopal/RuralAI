
import re
from collections import Counter

HIGH_RISK = ["chest pain","breathlessness","unconscious","blood","seizure"]
MODERATE = ["fever","cough","vomiting","diarrhea","severe headache"]
MILD = ["fatigue","cold","sore throat","body pain"]

def analyze_text(text):
    text = text.lower()
    found = []
    score = 0

    for word in HIGH_RISK:
        if word in text:
            found.append(word)
            score += 5

    for word in MODERATE:
        if word in text:
            found.append(word)
            score += 3

    for word in MILD:
        if word in text:
            found.append(word)
            score += 1

    duration = re.findall(r"(\d+\s*(day|days|week|weeks))", text)
    severity = "high" if "severe" in text else "normal"

    if score >= 8:
        level = "HIGH RISK"
    elif score >= 4:
        level = "MODERATE RISK"
    else:
        level = "LOW RISK"

    explanation = f"Detected symptoms: {', '.join(found)}. Severity: {severity}. Duration: {duration if duration else 'not specified'}."

    return {
        "risk": level,
        "score": score,
        "explanation": explanation
    }
