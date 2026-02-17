let riskChart = null;

/* ===============================
   ANALYZE FUNCTION
=================================*/

async function analyze() {
    const text = document.getElementById("symptoms").value.trim();
    const villageInput = document.getElementById("village");

    let village = "Unknown";
    if (villageInput) {
        village = villageInput.value.trim() || "Unknown";
    }

    if (!text) {
        alert("Please enter symptoms.");
        return;
    }

    try {
        const response = await fetch("/analyze", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                text: text,
                village: village
            })
        });

        if (!response.ok) {
            throw new Error("Server error");
        }

        const data = await response.json();

        displayResult(data);
        updateChart(data.risk_score);
        storeCaseLocally(data);

    } catch (error) {
        console.error(error);
        alert("AI analysis failed. Please try again.");
    }
}

/* ===============================
   DISPLAY RESULT
=================================*/

function displayResult(data) {
    const output = document.getElementById("output");

    let riskClass = "";
    if (data.risk_level === "HIGH RISK") riskClass = "high-risk";
    else if (data.risk_level === "MODERATE RISK") riskClass = "moderate-risk";
    else riskClass = "low-risk";

    output.innerHTML = `
        <div class="card">
            <h3 class="${riskClass}">Risk Level: ${data.risk_level}</h3>
            <p><strong>Risk Score:</strong> ${data.risk_score}</p>
            <p><strong>Detected Symptoms:</strong> ${data.explanation.detected_symptoms.join(", ") || "None"}</p>
            <p><strong>Severity Words:</strong> ${data.explanation.severity_words.join(", ") || "None"}</p>
            <p><strong>Duration:</strong> ${data.explanation.duration}</p>
            <p><strong>Emergency Flag:</strong> ${data.explanation.emergency_flag ? "Yes" : "No"}</p>
            <p><strong>Reasoning:</strong> ${data.explanation.risk_reasoning}</p>
        </div>
    `;
}

/* ===============================
   UPDATE CHART
=================================*/

function updateChart(score) {
    const ctx = document.getElementById("chart");

    if (!ctx) return;

    if (riskChart) {
        riskChart.destroy();
    }

    riskChart = new Chart(ctx, {
        type: "bar",
        data: {
            labels: ["Risk Score"],
            datasets: [{
                label: "AI Risk Score",
                data: [score],
                backgroundColor: score >= 20 ? "#ff4d4d"
                    : score >= 10 ? "#ffcc00"
                    : "#00ff99"
            }]
        },
        options: {
            scales: {
                y: {
                    beginAtZero: true
                }
            }
        }
    });
}

/* ===============================
   LOCAL STORAGE (Patient History)
=================================*/

function storeCaseLocally(data) {
    let history = JSON.parse(localStorage.getItem("ruralcare_cases") || "[]");
    history.unshift(data);
    localStorage.setItem("ruralcare_cases", JSON.stringify(history));
}

/* ===============================
   LOAD DOCTOR ANALYTICS
=================================*/

async function loadAnalytics() {
    try {
        const response = await fetch("/analytics");
        const data = await response.json();

        console.log("Analytics:", data);
        // You can expand this later for advanced dashboards

    } catch (error) {
        console.error("Analytics load failed");
    }
}

/* ===============================
   AUTO INIT
=================================*/

window.onload = function () {
    loadAnalytics();
};
