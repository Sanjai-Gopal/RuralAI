let chartInstance = null;

/* =========================================
   PATIENT NLP ANALYSIS
========================================= */

async function analyzeSymptoms() {
    const symptoms = document.getElementById("symptoms").value.trim();
    const resultDiv = document.getElementById("result");

    if (!symptoms) {
        alert("Please enter symptoms.");
        return;
    }

    try {
        const response = await fetch("/analyze", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ text: symptoms })
        });

        const data = await response.json();

        if (!response.ok) {
            alert(data.error);
            return;
        }

        displayPatientResult(data);

    } catch (error) {
        alert("Analysis failed. Try again.");
    }
}

/* =========================================
   DISPLAY PATIENT RESULT (NO SCORE)
========================================= */

function displayPatientResult(data) {
    const resultDiv = document.getElementById("result");

    let riskClass = "";
    if (data.risk_level === "HIGH RISK") riskClass = "high-risk";
    else if (data.risk_level === "MODERATE RISK") riskClass = "moderate-risk";
    else riskClass = "low-risk";

    resultDiv.innerHTML = `
        <div class="card">
            <h3 class="${riskClass}">Risk Level: ${data.risk_level}</h3>
            <p><strong>AI Suggestion:</strong></p>
            <p>${data.suggestion}</p>
            <p><em>This is not a medical diagnosis. Please consult a healthcare professional.</em></p>
        </div>
    `;
}

/* =========================================
   DOCTOR OVERRIDE
========================================= */

async function overrideCase(caseId) {
    const newRisk = prompt("Enter override risk (LOW RISK / MODERATE RISK / HIGH RISK)");

    if (!newRisk) return;

    const response = await fetch("/doctor/override", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            case_id: caseId,
            override: newRisk
        })
    });

    const data = await response.json();
    alert(data.status || data.error);
    location.reload();
}

/* =========================================
   LOAD ANALYTICS (DOCTOR)
========================================= */

async function loadAnalytics() {
    try {
        const response = await fetch("/analytics");
        const data = await response.json();

        const output = document.getElementById("analytics");

        output.innerHTML = `
            <div class="card">
                <h3>Total Cases: ${data.total_cases}</h3>
                <p><strong>Risk Distribution:</strong></p>
                <pre>${JSON.stringify(data.risk_distribution, null, 2)}</pre>
                <p><strong>Village Distribution:</strong></p>
                <pre>${JSON.stringify(data.village_distribution, null, 2)}</pre>
            </div>
        `;

    } catch (error) {
        console.error("Analytics load failed");
    }
}
