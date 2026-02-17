
async function analyze(){
let text = document.getElementById("symptoms").value;
if(!text){alert("Enter symptoms");return;}

let response = await fetch("/analyze",{
method:"POST",
headers:{"Content-Type":"application/json"},
body:JSON.stringify({text:text})
});

let data = await response.json();

document.getElementById("output").innerHTML =
"<b>Risk Level:</b> "+data.risk+
"<br><b>Score:</b> "+data.score+
"<br><b>Explanation:</b> "+data.explanation;

updateChart(data.score);
}

function updateChart(score){
new Chart(document.getElementById("chart"),{
type:'bar',
data:{
labels:["Risk Score"],
datasets:[{data:[score]}]
}
});
}
