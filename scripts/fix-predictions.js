import fs from "fs";

// 1. Read the CSV (You must temporarily place your CSV in data/kossu2026.csv)
const csvContent = fs.readFileSync("data/kossu2026.csv", "utf-8");
const lines = csvContent.trim().split("\n");
const dataLines = lines.slice(2); // Skip the 2 header rows

const players = [
  "Markus", "Juuso", "Pera", "Lari", "Erno", "Elmo",
  "Petri", "Tommi", "Severi", "Matti H", "Pasi", "Matti K"
];

// 2. Parse CSV matches
const csvMatches = [];
for (let i = 0; i < 48; i++) {
  const parts = dataLines[i].split(",");
  if (parts.length < 18) continue;
  
  const [datePart, timePart] = parts[0].split(" ");
  const [d, m, y] = datePart.split(".");
  const timestamp = new Date(`${y}-${m}-${d}T${timePart}:00+03:00`).getTime();
  
  const predictions = {};
  for (let j = 0; j < players.length; j++) {
    const pred = parts[6 + j].trim().toUpperCase();
    if (pred === "1" || pred === "X" || pred === "2") {
      predictions[players[j]] = pred;
    }
  }
  
  csvMatches.push({ timestamp, predictions });
}

// Sort CSV chronologically
csvMatches.sort((a, b) => a.timestamp - b.timestamp);

// 3. Read raw.json and sort chronologically
const raw = JSON.parse(fs.readFileSync("data/raw.json", "utf-8"));
const apiMatches = [...raw.matches].sort((a, b) => new Date(a.date).getTime() - new Date(b.date).getTime());

// 4. Map 1-to-1 based on chronological order
const fixedPredictions = {};
console.log("\n--- MAPPING PREDICTIONS TO CORRECT API IDs ---");
for (let i = 0; i < 48; i++) {
  const apiMatch = apiMatches[i];
  const csvMatch = csvMatches[i];
  
  if (apiMatch && csvMatch) {
    fixedPredictions[apiMatch.id] = csvMatch.predictions;
    console.log(`✅ Mapped API ID ${apiMatch.id} (${apiMatch.homeTeam} vs ${apiMatch.awayTeam})`);
  }
}

// 5. Save the fixed predictions
fs.writeFileSync("data/predictions.json", JSON.stringify(fixedPredictions, null, 2));
console.log("\n🎉 predictions.json has been fixed!");
